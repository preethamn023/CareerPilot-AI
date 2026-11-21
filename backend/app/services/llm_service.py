"""LLM provider abstraction.

Provider priority:
1. Google Gemini (official `google-genai` SDK) - used when GEMINI_API_KEY is set.
   Supports native structured JSON output and native function/tool calling.
2. Local AI bridge (mini-services/ai-bridge wrapping z-ai-web-dev-sdk) - used
   when no Gemini key is configured so the application remains fully
   functional in the demo sandbox. JSON and tool choice are implemented via
   strict prompting + robust parsing.
3. None -> callers fall back to deterministic rule-based analysis.

All provider failures are converted into user-safe LLMError messages; API
keys are never included in any exception text or log.
"""
from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from typing import Any, TypeVar

import httpx
from pydantic import BaseModel, ValidationError

from app.config import settings
from app.services.exceptions import LLMError, LLMNotConfiguredError

T = TypeVar("T", bound=BaseModel)

GEMINI_PROVIDER = "gemini"
BRIDGE_PROVIDER = "glm_bridge"
NONE_PROVIDER = "none"

_BRIDGE_UNAVAILABLE_TTL = 30.0


@dataclass
class ToolSpec:
    """Provider-agnostic description of a callable tool."""

    name: str
    description: str
    parameters: dict[str, Any] = field(default_factory=dict)  # JSON-schema style
    required: list[str] = field(default_factory=list)


@dataclass
class ToolAction:
    """The LLM's decision to call one tool with validated arguments."""

    tool: str
    arguments: dict[str, Any] = field(default_factory=dict)


class LLMService:
    def __init__(self) -> None:
        self._gemini_client: Any | None = None
        self._bridge_checked_at: float = 0.0
        self._bridge_available: bool | None = None

    # ------------------------------------------------------------ status
    def provider_status(self) -> dict[str, Any]:
        provider, model = self._active_provider()
        return {
            "provider": provider,
            "configured": provider != NONE_PROVIDER,
            "model": model,
        }

    def _active_provider(self) -> tuple[str, str | None]:
        if settings.gemini_api_key:
            return GEMINI_PROVIDER, settings.gemini_model
        if settings.ai_bridge_enabled and self._bridge_is_available():
            return BRIDGE_PROVIDER, "glm-4.x (local sandbox bridge)"
        return NONE_PROVIDER, None

    def require_provider(self) -> str:
        provider, _ = self._active_provider()
        if provider == NONE_PROVIDER:
            raise LLMNotConfiguredError(
                "No AI provider is configured. Set GEMINI_API_KEY in the root .env "
                "to enable AI-powered analysis. The application is currently "
                "running in rule-based mode."
            )
        return provider

    # ------------------------------------------------------- gemini client
    def _get_gemini_client(self) -> Any:
        if self._gemini_client is None:
            from google import genai  # imported lazily so rule-based mode works without the SDK

            self._gemini_client = genai.Client(api_key=settings.gemini_api_key)
        return self._gemini_client

    # ------------------------------------------------------- bridge client
    def _bridge_is_available(self) -> bool:
        now = time.monotonic()
        if self._bridge_available is not None and now - self._bridge_checked_at < _BRIDGE_UNAVAILABLE_TTL:
            return self._bridge_available
        try:
            response = httpx.get(
                f"{settings.ai_bridge_url}/health",
                timeout=2.0,
            )
            self._bridge_available = response.status_code == 200
        except httpx.HTTPError:
            self._bridge_available = False
        self._bridge_checked_at = now
        return self._bridge_available

    def _bridge_chat(self, messages: list[dict[str, str]], temperature: float) -> str:
        try:
            response = httpx.post(
                f"{settings.ai_bridge_url}/v1/chat/completions",
                json={"messages": messages, "temperature": temperature},
                timeout=settings.ai_bridge_timeout_seconds,
            )
            response.raise_for_status()
            payload = response.json()
        except httpx.HTTPError as exc:
            self._bridge_available = False
            self._bridge_checked_at = time.monotonic()
            raise LLMError(
                "The local AI service is not responding. Falling back to "
                "rule-based mode; restart the ai-bridge mini-service to restore AI features."
            ) from exc
        content = payload.get("content")
        if not content or not isinstance(content, str):
            raise LLMError("The AI service returned an empty response.")
        return content

    # ------------------------------------------------------------- chat
    def chat(
        self,
        messages: list[dict[str, str]],
        temperature: float | None = None,
    ) -> str:
        """Single-turn completion. `messages` uses OpenAI-style roles."""
        provider, _ = self._active_provider()
        temp = settings.gemini_temperature if temperature is None else temperature

        if provider == GEMINI_PROVIDER:
            return self._gemini_chat(messages, temp)
        if provider == BRIDGE_PROVIDER:
            return self._bridge_chat(messages, temp)
        raise LLMNotConfiguredError(
            "No AI provider is configured. Set GEMINI_API_KEY in the root .env "
            "to enable AI features."
        )

    def _gemini_chat(self, messages: list[dict[str, str]], temperature: float) -> str:
        from google.genai import types

        client = self._get_gemini_client()
        system = "\n".join(m["content"] for m in messages if m["role"] == "system")
        contents = [m["content"] for m in messages if m["role"] != "system"]
        try:
            response = client.models.generate_content(
                model=settings.gemini_model,
                contents=contents,
                config=types.GenerateContentConfig(
                    system_instruction=system or None,
                    temperature=temperature,
                    max_output_tokens=settings.ai_max_output_tokens,
                ),
            )
        except Exception as exc:  # noqa: BLE001 - never leak key details
            raise self._translate_gemini_error(exc) from exc
        text = getattr(response, "text", None)
        if not text:
            raise LLMError("Gemini returned an empty response. Please try again.")
        return text

    # ---------------------------------------------------- structured JSON
    def complete_json(
        self,
        schema: type[T],
        system: str,
        user: str,
        temperature: float | None = None,
    ) -> T:
        """Ask the active provider for a structured JSON response and
        validate it against `schema`. One retry on invalid JSON/output."""
        provider, _ = self._active_provider()
        if provider == NONE_PROVIDER:
            raise LLMNotConfiguredError(
                "No AI provider is configured. Set GEMINI_API_KEY in the root .env "
                "to enable AI features."
            )

        if provider == GEMINI_PROVIDER:
            return self._gemini_json(schema, system, user, temperature)

        # Bridge provider: prompt-strict JSON + lenient parsing.
        schema_json = json.dumps(schema.model_json_schema(), indent=2)
        strict_system = (
            f"{system}\n\nCRITICAL OUTPUT CONTRACT: Respond with a single valid "
            f"JSON object only. No markdown, no code fences, no commentary. "
            f"The JSON must validate against this JSON schema:\n{schema_json}"
        )
        last_error: Exception | None = None
        for attempt in range(2):
            prompt = user
            if attempt == 1 and last_error is not None:
                prompt = (
                    f"{user}\n\nYour previous response was invalid: {last_error}. "
                    "Return ONLY the corrected JSON object."
                )
            try:
                raw = self._bridge_chat(
                    [{"role": "system", "content": strict_system}, {"role": "user", "content": prompt}],
                    settings.gemini_temperature if temperature is None else temperature,
                )
                data = loads_lenient_json(raw)
                return schema.model_validate(data)
            except (LLMError, json.JSONDecodeError) as exc:
                last_error = exc
            except ValidationError as exc:
                last_error = exc
        raise LLMError(
            "The AI returned an invalid response after retries. Please try again."
        )

    def _gemini_json(
        self,
        schema: type[T],
        system: str,
        user: str,
        temperature: float | None,
    ) -> T:
        from google.genai import types

        client = self._get_gemini_client()
        try:
            response = client.models.generate_content(
                model=settings.gemini_model,
                contents=[user],
                config=types.GenerateContentConfig(
                    system_instruction=system or None,
                    temperature=settings.gemini_temperature if temperature is None else temperature,
                    response_mime_type="application/json",
                    response_schema=schema,
                    max_output_tokens=settings.ai_max_output_tokens,
                ),
            )
        except Exception as exc:  # noqa: BLE001
            raise self._translate_gemini_error(exc) from exc

        text = getattr(response, "text", None)
        if not text:
            raise LLMError("Gemini returned an empty response. Please try again.")
        try:
            data = json.loads(text)
        except json.JSONDecodeError as exc:
            # Retry once with lenient parsing before failing.
            try:
                data = loads_lenient_json(text)
            except json.JSONDecodeError:
                raise LLMError("The AI returned malformed JSON. Please try again.") from exc
        try:
            return schema.model_validate(data)
        except ValidationError as exc:
            raise LLMError(
                "The AI response did not match the expected structure. Please try again."
            ) from exc

    # -------------------------------------------------- agent tool choice
    def choose_tool(
        self,
        system: str,
        conversation: list[dict[str, str]],
        tools: list[ToolSpec],
        temperature: float = 0.0,
    ) -> ToolAction | str:
        """Ask the model to select the next tool, or produce a final answer.

        Returns ToolAction when a tool call is requested, otherwise the
        final-answer text."""
        provider, _ = self._active_provider()
        if provider == NONE_PROVIDER:
            raise LLMNotConfiguredError("No AI provider configured for agent mode.")

        if provider == GEMINI_PROVIDER:
            return self._gemini_choose_tool(system, conversation, tools, temperature)
        return self._bridge_choose_tool(system, conversation, tools, temperature)

    def _gemini_choose_tool(
        self,
        system: str,
        conversation: list[dict[str, str]],
        tools: list[ToolSpec],
        temperature: float,
    ) -> ToolAction | str:
        """Native Gemini function calling."""
        from google.genai import types

        declarations = [
            types.FunctionDeclaration(
                name=tool.name,
                description=tool.description,
                parameters=tool.parameters or {"type": "object", "properties": {}},
            )
            for tool in tools
        ]
        config = types.GenerateContentConfig(
            system_instruction=system,
            temperature=temperature,
            tools=[types.Tool(function_declarations=declarations)],
            max_output_tokens=settings.ai_max_output_tokens,
        )
        gemini_contents = [
            types.Content(
                role="model" if msg.get("role") == "assistant" else "user",
                parts=[types.Part.from_text(text=msg.get("content", ""))],
            )
            for msg in conversation
            if msg.get("role") != "system"
        ]
        client = self._get_gemini_client()
        try:
            response = client.models.generate_content(
                model=settings.gemini_model,
                contents=gemini_contents,
                config=config,
            )
        except Exception as exc:  # noqa: BLE001
            raise self._translate_gemini_error(exc) from exc

        function_calls = getattr(response, "function_calls", None)
        if function_calls:
            call = function_calls[0]
            return ToolAction(tool=call.name, arguments=dict(call.args or {}))
        text = getattr(response, "text", None)
        if text:
            return text
        raise LLMError("Gemini returned neither a tool call nor a final answer.")

    def _bridge_choose_tool(
        self,
        system: str,
        conversation: list[dict[str, str]],
        tools: list[ToolSpec],
        temperature: float,
    ) -> ToolAction | str:
        """Prompt-based tool choice for the bridge provider."""
        tool_specs = json.dumps(
            [
                {"name": t.name, "description": t.description, "parameters": t.parameters or {}}
                for t in tools
            ],
            indent=2,
        )
        tool_system = (
            f"{system}\n\nYou are an agent that must select ONE action. Available tools:\n"
            f"{tool_specs}\n\nRespond with a single JSON object and nothing else, either:\n"
            '{"tool": "<tool name>", "arguments": { ... }}\n'
            "to call a tool, or:\n"
            '{"final_answer": "<your complete answer to the user>"}\n'
            "when no further tool call is needed. Never invent tool names or arguments."
        )
        raw = self._bridge_chat(
            [{"role": "system", "content": tool_system}, *conversation],
            temperature,
        )
        try:
            data = loads_lenient_json(raw)
        except json.JSONDecodeError:
            return raw  # treat unparseable output as a final answer
        if isinstance(data, dict):
            if data.get("tool"):
                return ToolAction(tool=str(data["tool"]), arguments=data.get("arguments") or {})
            if data.get("final_answer"):
                return str(data["final_answer"])
        return raw

    # ------------------------------------------------------------- utils
    @staticmethod
    def _translate_gemini_error(exc: Exception) -> LLMError:
        text = str(exc).lower()
        if "api key" in text or "permission" in text or "unauthenticated" in text:
            return LLMError("The Gemini API key is invalid or lacks permission. Check GEMINI_API_KEY.")
        if "quota" in text or "rate" in text or "429" in text:
            return LLMError("Gemini quota or rate limit reached. Please wait a moment and retry.")
        if "timeout" in text or "deadline" in text:
            return LLMError("The Gemini request timed out. Please try again.")
        if "not found" in text or "404" in text:
            return LLMError(
                "The configured GEMINI_MODEL is not available. Update the model name in the root .env."
            )
        return LLMError("The Gemini request failed. Please try again.")


def loads_lenient_json(raw: str) -> Any:
    """Parse JSON that may be wrapped in markdown fences or prose."""
    text = raw.strip()
    # Strip code fences.
    if text.startswith("```"):
        text = text.strip("`")
        if text.lower().startswith("json"):
            text = text[4:]
        text = text.strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    # Fall back to the outermost brace/bracket span.
    start = min(
        (i for i in (text.find("{"), text.find("[")) if i != -1),
        default=-1,
    )
    if start == -1:
        raise json.JSONDecodeError("no JSON object found", text, 0)
    end = max(text.rfind("}"), text.rfind("]"))
    candidate = text[start : end + 1]
    return json.loads(candidate)


llm_service = LLMService()
