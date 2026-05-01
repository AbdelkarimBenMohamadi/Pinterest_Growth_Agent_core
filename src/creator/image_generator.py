import httpx
import hashlib
import logging
import urllib.parse
from pathlib import Path
from src.models import ContentBrief

logger = logging.getLogger(__name__)


def _get_negative_prompts() -> str:
    path = Path("negative_prompts.txt")
    if path.exists():
        lines = [line.strip() for line in path.read_text(encoding="utf-8").splitlines() if line.strip() and not line.startswith("#")]
        if lines:
            # Join all uncommented lines into a single comma-separated string
            return ", ".join(lines)
    return "people, person, woman, female, face, humans"


async def generate_image(brief: ContentBrief, config: dict, retry: bool = False) -> tuple[str, str]:
    """
    Generate a Pinterest pin image via Pollinations.ai.
    Returns (image_path, image_hash).
    Falls back to Together AI, then Hugging Face if Pollinations is down.
    If retry=True, adds variation suffix to get a different image.
    """
    suffix = " modern clean style" if retry else ""
    negative = _get_negative_prompts()
    positive_prompt = f"Pinterest pin style, {brief.target_keyword}, professional photography, 2:3 vertical, clean composition{suffix}"

    comfy_cfg = config.get("comfyui", {})
    if comfy_cfg.get("enabled", False):
        try:
            logger.info("ComfyUI enabled, trying local generation first...")
            image_bytes = await _comfyui_fallback(positive_prompt, config, negative=negative)
        except Exception as e:
            logger.warning(f"ComfyUI failed: {e}. Falling back to Pollinations.ai...")
            try:
                image_bytes = await _pollinations_generate(positive_prompt, negative=negative)
            except httpx.HTTPError as e2:
                logger.warning(f"Pollinations.ai failed: {e2}. Trying Together AI fallback...")
                try:
                    image_bytes = await _together_fallback(positive_prompt, config, negative=negative)
                except httpx.HTTPError:
                    logger.warning("Together AI failed. Trying Hugging Face fallback...")
                    image_bytes = await _huggingface_fallback(positive_prompt, config, negative=negative)
    else:
        try:
            image_bytes = await _pollinations_generate(positive_prompt, negative=negative)
        except httpx.HTTPError as e:
            logger.warning(f"Pollinations.ai failed: {e}. Trying Together AI fallback...")
            try:
                image_bytes = await _together_fallback(positive_prompt, config, negative=negative)
            except httpx.HTTPError:
                logger.warning("Together AI failed. Trying Hugging Face fallback...")
                image_bytes = await _huggingface_fallback(positive_prompt, config, negative=negative)

    image_hash = hashlib.sha256(image_bytes).hexdigest()

    assets_dir = Path(config.get("paths", {}).get("assets_dir", "assets"))
    assets_dir.mkdir(parents=True, exist_ok=True)
    image_path = str(assets_dir / f"{image_hash}.png")

    Path(image_path).write_bytes(image_bytes)
    logger.info(f"Generated image: {image_path}")
    return image_path, image_hash


async def _pollinations_generate(prompt: str, negative: str = "") -> bytes:
    """Primary: Pollinations.ai — free, no key."""
    encoded = urllib.parse.quote(prompt)
    url = f"https://image.pollinations.ai/prompt/{encoded}"

    async with httpx.AsyncClient(timeout=90.0, follow_redirects=True) as client:
        params = {"width": 1000, "height": 1500, "nologo": "true"}
        if negative:
            params["negative"] = negative
        response = await client.get(url, params=params)
        response.raise_for_status()
        return response.content


async def _together_fallback(prompt: str, config: dict, negative: str = "") -> bytes:
    """
    Fallback: Together AI FLUX.1 schnell (free endpoint).
    Only used if Pollinations is down. Requires TOGETHER_API_KEY in .env.
    If no key is set, raises an error.
    """
    from src.utils.config import get_together_api_key
    api_key = get_together_api_key()
    if not api_key:
        raise Exception("Pollinations.ai is down and no TOGETHER_API_KEY is set in .env")

    async with httpx.AsyncClient(timeout=60.0) as client:
        json_body = {
            "model": "black-forest-labs/FLUX.1-schnell-Free",
            "prompt": prompt,
            "width": 1024,
            "height": 1536,
            "n": 1,
        }
        if negative:
            json_body["negative_prompt"] = negative
        response = await client.post(
            "https://api.together.xyz/v1/images/generations",
            headers={"Authorization": f"Bearer {api_key}"},
            json=json_body
        )
        response.raise_for_status()
        image_url = response.json()["data"][0]["url"]
        img_response = await client.get(image_url)
        return img_response.content


async def _huggingface_fallback(prompt: str, config: dict, negative: str = "") -> bytes:
    """
    Final fallback: Hugging Face Inference API (free tier).
    Requires HF_API_KEY in .env. Uses stabilityai/stable-diffusion-xl-base-1.0.
    """
    from src.utils.config import get_huggingface_api_key
    api_key = get_huggingface_api_key()
    if not api_key:
        raise Exception("Pollinations.ai and Together AI failed, and no HF_API_KEY is set in .env")

    async with httpx.AsyncClient(timeout=120.0) as client:
        response = await client.post(
            "https://api-inference.huggingface.co/models/stabilityai/stable-diffusion-xl-base-1.0",
            headers={"Authorization": f"Bearer {api_key}"},
            json={
                "inputs": prompt,
                "parameters": {
                    "negative_prompt": negative if negative else None,
                    "width": 1024,
                    "height": 1536,
                    "num_inference_steps": 30,
                }
            }
        )
        response.raise_for_status()
        return response.content


async def _comfyui_fallback(prompt: str, config: dict, negative: str = "") -> bytes:
    """
    Final local fallback: ComfyUI REST API with SDXL.
    Sends a text2img workflow via API and retrieves the generated image.
    Uses settings from config.yaml under the 'comfyui' block if provided.
    """
    import asyncio
    import time

    comfy_cfg = config.get("comfyui", {})
    host = comfy_cfg.get("host", "127.0.0.1")
    port = comfy_cfg.get("port", 8188)
    model_name = comfy_cfg.get("model", "sd_xl_base_1.0.safetensors")

    comfy_url = f"http://{host}:{port}"

    workflow = {
        "3": {
            "inputs": {"width": 1024, "height": 1536, "batch_size": 1},
            "class_type": "EmptyLatentImage"
        },
        "41": {
            "inputs": {
                "text": prompt,
                "clip": ["12", 1]
            },
            "class_type": "CLIPTextEncode"
        },
        "51": {
            "inputs": {
                "text": negative if negative else "",
                "clip": ["12", 1]
            },
            "class_type": "CLIPTextEncode"
        },
        "6": {
            "inputs": {
                "seed": int(time.time() * 1000) % 1000000000000000,
                "steps": 25,
                "cfg": 7.0,
                "sampler_name": "euler",
                "scheduler": "normal",
                "positive": ["41", 0],
                "negative": ["51", 0],
                "latent_image": ["3", 0],
                "model": ["12", 0],
                "denoise": 1.0
            },
            "class_type": "KSampler"
        },
        "7": {
            "inputs": {
                "samples": ["6", 0],
                "vae": ["12", 2]
            },
            "class_type": "VAEDecode"
        },
        "8": {
            "inputs": {
                "images": ["7", 0],
                "filename_prefix": "pga_pin"
            },
            "class_type": "SaveImage"
        },
        "12": {
            "inputs": {
                "ckpt_name": model_name
            },
            "class_type": "CheckpointLoaderSimple"
        }
    }

    async with httpx.AsyncClient(timeout=180.0) as client:
        resp = await client.post(f"{comfy_url}/prompt", json={"prompt": workflow})
        resp.raise_for_status()
        result = resp.json()
        prompt_id = result.get("prompt_id", "")

        for _ in range(90):
            await asyncio.sleep(2)
            history_resp = await client.get(f"{comfy_url}/history/{prompt_id}")
            if history_resp.status_code == 200:
                history = history_resp.json()
                if prompt_id in history and history[prompt_id].get("outputs"):
                    outputs = history[prompt_id]["outputs"]
                    for node_id, node_output in outputs.items():
                        if "images" in node_output:
                            image_data = node_output["images"][0]
                            image_resp = await client.get(
                                f"{comfy_url}/view",
                                params={
                                    "filename": image_data["filename"],
                                    "type": "output",
                                    "subfolder": image_data.get("subfolder", "")
                                }
                            )
                            image_resp.raise_for_status()
                            return image_resp.content
            await asyncio.sleep(2)

    raise Exception("ComfyUI image generation timed out")