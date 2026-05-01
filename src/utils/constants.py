from pathlib import Path

SESSION_FILE = Path("data/pinterest_session.json")

IMAGE_PROMPT_SUFFIX = "modern clean style"
IMAGE_NEGATIVE_PROMPT = "people, person, woman, man, female, male, face, humans, text, letters, watermark, signature, ugly, bad proportions, bad anatomy, blur"

MIN_KEYWORD_LENGTH = 3
MAX_KEYWORD_LENGTH = 50
MAX_RELATED_TERMS = 15

DIAGNOSTIC_CONSECUTIVE_FAILURES = 3
DIAGNOSTIC_LOW_RESULTS = 3
DIAGNOSTIC_AVG_RESULTS_THRESHOLD = 2.0

SCRAPE_TIMEOUT = 30
SCRAPE_DELAY = 4
AUTOCOMPLETE_DELAY = 2

PUBLISH_TIMEOUT = 20
PIN_CREATION_PATTERNS = [
    "/v3/pins",
    "pinresource/create",
    "pin-builder",
    "/resource/pin",
]

HOURLY_POST_LIMIT = 2

COOLDOWN_DEFAULT_HOURS = 48
SHADOWBAN_CHECK_VELOCITY = 1.0
TREND_BOOST_THRESHOLD = 2.0

DAILY_LIMITS = {
    (0, 7): {"max_pins": 1, "max_actions": 10},
    (8, 14): {"max_pins": 2, "max_actions": 20},
    (15, 30): {"max_pins": 5, "max_actions": 40},
    (31, 9999): {"max_pins": 8, "max_actions": 60},
}
