from app.config import get_settings
from app.core.encryption import decrypt_value, encrypt_value, mask_api_key
from app.services.model_config_service import validate_base_url


def test_encrypt_decrypt_roundtrip():
    settings = get_settings()
    if not settings.encryption_key:
        settings.encryption_key = "test-encryption-key-32chars-000000"

    original = "sk-1234567890"
    encrypted = encrypt_value(original)
    assert encrypted != original
    assert decrypt_value(encrypted) == original


def test_mask_api_key():
    assert mask_api_key("sk-1234567890") == "sk-****7890"
    assert mask_api_key("short") == "****"


def test_validate_base_url():
    assert validate_base_url("https://api.deepseek.com")
    assert not validate_base_url("http://127.0.0.1")
    assert not validate_base_url("http://localhost")
    assert not validate_base_url("ftp://example.com")
