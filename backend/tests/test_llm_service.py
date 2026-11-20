"""Tests: LLM service provider behaviour (no key, bridge, JSON parsing)."""
from __future__ import annotations

import json

import pytest
from pydantic import BaseModel

from app.services.exceptions import LLMError, LLMNotConfiguredError
from app.services.llm_service import LLMService, loads_lenient_json


class Person(BaseModel):
    name: str
    age: int


class TestNoProvider:
    def test_provider_status_is_none(self) -> None:
        service = LLMService()
        status = service.provider_status()
        assert status["provider"] == "none"
        assert status["configured"] is False

    def test_chat_raises_not_configured(self) -> None:
        service = LLMService()
        with pytest.raises(LLMNotConfiguredError) as exc_info:
            service.chat([{"role": "user", "content": "hi"}])
        assert "GEMINI_API_KEY" in str(exc_info.value)

    def test_complete_json_raises_not_configured(self) -> None:
        service = LLMService()
        with pytest.raises(LLMNotConfiguredError):
            service.complete_json(Person, "sys", "user")

    def test_safe_error_message_no_key_material(self) -> None:
        """Error text must never contain key-like material."""
        from app.services.exceptions import CareerPilotError

        service = LLMService()
        try:
            service.chat([{"role": "user", "content": "hi"}])
        except CareerPilotError as exc:
            assert "AIza" not in str(exc)


class TestLenientJson:
    def test_plain_json(self) -> None:
        assert loads_lenient_json('{"a": 1}') == {"a": 1}

    def test_fenced_json(self) -> None:
        assert loads_lenient_json('```json\n{"a": 1}\n```') == {"a": 1}

    def test_fenced_without_language(self) -> None:
        assert loads_lenient_json('```\n{"a": 1}\n```') == {"a": 1}

    def test_json_wrapped_in_prose(self) -> None:
        text = 'Here is the result: {"name": "Rahul", "age": 22} hope it helps!'
        assert loads_lenient_json(text) == {"name": "Rahul", "age": 22}

    def test_invalid_raises(self) -> None:
        with pytest.raises(json.JSONDecodeError):
            loads_lenient_json("no json here at all")


class TestBridgeProvider:
    def _bridge_service(self, monkeypatch: pytest.MonkeyPatch, responses: list[str]) -> LLMService:
        from app.config import settings

        service = LLMService()
        monkeypatch.setattr(settings, "ai_bridge_enabled", True)
        monkeypatch.setattr(service, "_bridge_is_available", lambda: True)

        calls = {"n": 0}

        def fake_bridge_chat(messages, temperature):  # noqa: ANN001, ARG001
            response = responses[min(calls["n"], len(responses) - 1)]
            calls["n"] += 1
            return response

        monkeypatch.setattr(service, "_bridge_chat", fake_bridge_chat)
        return service

    def test_complete_json_validates_response(self, monkeypatch: pytest.MonkeyPatch) -> None:
        service = self._bridge_service(monkeypatch, ['{"name": "Rahul", "age": 22}'])
        person = service.complete_json(Person, "system prompt", "user prompt")
        assert person.name == "Rahul"
        assert person.age == 22

    def test_complete_json_retries_on_malformed_then_succeeds(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        service = self._bridge_service(
            monkeypatch,
            ["oops not json", '```json\n{"name": "Asha", "age": 21}\n```'],
        )
        person = service.complete_json(Person, "s", "u")
        assert person.name == "Asha"

    def test_complete_json_fails_after_retries(self, monkeypatch: pytest.MonkeyPatch) -> None:
        service = self._bridge_service(monkeypatch, ["still not json"])
        with pytest.raises(LLMError) as exc_info:
            service.complete_json(Person, "s", "u")
        assert "invalid response" in str(exc_info.value).lower()

    def test_complete_json_retries_on_validation_error(self, monkeypatch: pytest.MonkeyPatch) -> None:
        service = self._bridge_service(
            monkeypatch,
            ['{"name": "Wrong types here", "age": "not-a-number"}', '{"name": "Fixed", "age": 30}'],
        )
        person = service.complete_json(Person, "s", "u")
        assert person.age == 30

    def test_bridge_connection_error_becomes_safe_llm_error(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        import httpx

        service = LLMService()

        def failing_post(*args, **kwargs):  # noqa: ANN001, ARG001
            raise httpx.ConnectError("connection refused to 127.0.0.1:8010")

        monkeypatch.setattr(httpx, "post", failing_post)
        monkeypatch.setattr(service, "_bridge_is_available", lambda: True)
        with pytest.raises(LLMError) as exc_info:
            service._bridge_chat([{"role": "user", "content": "hi"}], 0.2)
        assert "127.0.0.1" not in str(exc_info.value) or "not responding" in str(exc_info.value)
