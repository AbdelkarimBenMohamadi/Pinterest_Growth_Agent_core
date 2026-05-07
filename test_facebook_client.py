import pytest
from src.worker.facebook_client import FacebookClient

def test_facebook_client_init():
    config = {"browser": {"headless": True}}
    client = FacebookClient(config)
    assert client.config == config
    assert client._playwright is None
    assert client._browser is None
