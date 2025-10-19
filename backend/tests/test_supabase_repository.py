import pytest
from fastapi import status

from backend.app.config import Settings
from backend.app.services.supabase import SupabaseApiError, SupabaseRepository


class DummyClient:
    def __init__(self) -> None:
        self.closed = False

    def request(self, *args, **kwargs):
        raise AssertionError("No HTTP calls expected in tests")

    def close(self) -> None:
        self.closed = True


def _settings(**kwargs) -> Settings:
    defaults = {
        "supabase_url": "https://example.supabase.co",
        "supabase_service_role_key": "service-role",
    }
    defaults.update(kwargs)
    return Settings(**defaults)


def test_supabase_repository_initialises_with_configured_settings() -> None:
    repo = SupabaseRepository(settings=_settings(), client=DummyClient())
    assert repo._headers["apikey"] == "service-role"
    assert repo._headers["Authorization"] == "Bearer service-role"


def test_supabase_repository_uses_anon_key_when_service_role_missing() -> None:
    settings = _settings(supabase_service_role_key=None, supabase_anon_key="anon-key")
    repo = SupabaseRepository(settings=settings, client=DummyClient())
    assert repo._headers["apikey"] == "anon-key"
    assert repo._headers["Authorization"] == "Bearer anon-key"


def test_supabase_repository_raises_when_supabase_disabled() -> None:
    settings = Settings()
    with pytest.raises(SupabaseApiError) as excinfo:
        SupabaseRepository(settings=settings, client=DummyClient())

    assert excinfo.value.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
    assert "not configured" in excinfo.value.detail
