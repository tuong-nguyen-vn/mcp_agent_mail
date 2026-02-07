"""LiteLLM integration: router, caching, and cost tracking.

Centralizes LLM usage behind a minimal async helper. Providers + API keys
are configured via environment variables; configuration toggles come from
python-decouple in `config.py`.

NOTE: ``litellm`` is imported **lazily** (inside functions that need it)
to avoid a ~11-second startup penalty on every CLI invocation.
"""

from __future__ import annotations

import asyncio
import contextlib
import os
import socket
from dataclasses import dataclass
from typing import Any, Optional
from urllib.parse import urlparse

import structlog
from decouple import Config as DecoupleConfig, RepositoryEnv

from .config import get_settings

_router: Optional[Any] = None
_init_lock = asyncio.Lock()
_initialized: bool = False
_logger = structlog.get_logger(__name__)


@dataclass(slots=True, frozen=True)
class LlmOutput:
    content: str
    model: str
    provider: str | None
    estimated_cost_usd: float | None = None


def _get_litellm() -> Any:
    """Lazy-import litellm to avoid 11+ second module-level cost."""
    import litellm as _litellm
    return _litellm


def _existing_callbacks() -> list[Any]:
    _litellm = _get_litellm()
    callbacks = getattr(_litellm, "success_callback", []) or []
    return list(callbacks)


def _setup_callbacks() -> None:
    settings = get_settings()
    if not settings.llm.cost_logging_enabled:
        return

    def _on_success(kwargs: dict[str, Any], completion_response: Any, start_time: float, end_time: float) -> None:
        try:
            cost = float(kwargs.get("response_cost", 0.0) or 0.0)
            model = str(kwargs.get("model", ""))
            if cost > 0:
                if settings.log_rich_enabled:
                    try:
                        import importlib as _imp
                        _rc = _imp.import_module("rich.console")
                        _rp = _imp.import_module("rich.panel")
                        _rt = _imp.import_module("rich.text")
                        Console = _rc.Console
                        Panel = _rp.Panel
                        Text = _rt.Text

                        body = Text.assemble(
                            ("model: ", "cyan"), (model, "white"), "\n",
                            ("cost: ", "cyan"), (f"${cost:.6f}", "bold green"),
                        )
                        Console().print(Panel(body, title="llm: cost", border_style="magenta"))
                    except Exception:
                        _logger.info("litellm.cost", model=model, cost_usd=cost)
                else:
                    _logger.info("litellm.cost", model=model, cost_usd=cost)
        except Exception:
            pass

    _litellm = _get_litellm()
    if _on_success not in _existing_callbacks():
        callbacks: list[Any] = [*_existing_callbacks(), _on_success]
        with contextlib.suppress(Exception):
            _litellm.success_callback = callbacks


async def _ensure_initialized() -> None:
    global _router, _initialized
    if _initialized:
        return
    async with _init_lock:
        if _initialized:
            return
        settings = get_settings()
        _litellm = _get_litellm()

        try:
            _bridge_provider_env()
        except Exception:
            _logger.debug("litellm.env.bridge_failed")

        if settings.llm.cache_enabled:
            from litellm.types.caching import LiteLLMCacheType
            with contextlib.suppress(Exception):
                backend = (getattr(settings.llm, "cache_backend", "local") or "local").lower()
                if backend == "redis" and getattr(settings.llm, "cache_redis_url", ""):
                    parsed = urlparse(settings.llm.cache_redis_url)
                    host = parsed.hostname or "localhost"
                    port = str(parsed.port or "6379")
                    pwd = parsed.password or None
                    try:
                        socket.gethostbyname(host)
                        _litellm.enable_cache(
                            type=LiteLLMCacheType.REDIS,
                            host=str(host),
                            port=str(port),
                            password=pwd,
                        )
                    except Exception:
                        _logger.info("litellm.cache.redis_unavailable_fallback_local", host=host, port=port)
                        _litellm.enable_cache(type=LiteLLMCacheType.LOCAL)
                else:
                    _litellm.enable_cache(type=LiteLLMCacheType.LOCAL)

        _setup_callbacks()

        _router = None
        _initialized = True


def _choose_best_available_model(preferred: str) -> str:
    """Select a provider/model that is likely to be available based on configured API keys.

    If a concrete provider is not implied by the preferred name (e.g. 'gpt-5-mini'),
    pick a small, low-cost model for whatever provider keys are available.
    """
    env = os.environ

    if "/" in preferred or ":" in preferred:
        return preferred

    if env.get("OPENAI_API_KEY"):
        return "gpt-4o-mini"
    if env.get("GOOGLE_API_KEY"):
        return "gemini-1.5-flash"
    if env.get("ANTHROPIC_API_KEY"):
        return "claude-3-haiku-20240307"
    if env.get("GROQ_API_KEY"):
        return "groq/llama-3.1-70b-versatile"
    if env.get("DEEPSEEK_API_KEY"):
        return "deepseek/deepseek-chat"
    if env.get("XAI_API_KEY"):
        return "xai/grok-2-mini"
    if env.get("OPENROUTER_API_KEY"):
        return "openrouter/openai/gpt-4o-mini"
    return preferred


def _resolve_model_alias(name: str) -> str:
    """Map known placeholder or project-specific names to concrete provider models."""
    normalized = (name or "").strip().lower()
    if normalized in {"gpt-5-mini", "gpt5-mini", "gpt-5m", "gpt-4o-mini"}:
        return _choose_best_available_model(normalized)
    return name

async def complete_system_user(system: str, user: str, *, model: Optional[str] = None, temperature: Optional[float] = None, max_tokens: Optional[int] = None) -> LlmOutput:
    """Chat completion helper returning content.

    Falls back to litellm.completion if Router isn't available.
    """
    global _router
    await _ensure_initialized()
    _litellm = _get_litellm()
    settings = get_settings()
    use_model = model or settings.llm.default_model
    use_model = _resolve_model_alias(use_model)
    temp = settings.llm.temperature if temperature is None else float(temperature)
    mtoks = settings.llm.max_tokens if max_tokens is None else int(max_tokens)

    messages = [
        {"role": "system", "content": system},
        {"role": "user", "content": user},
    ]

    def _call_router(router: Any) -> Any:
        return router.completion(model=use_model, messages=messages, temperature=temp, max_tokens=mtoks)

    def _call_direct() -> Any:
        return _litellm.completion(model=use_model, messages=messages, temperature=temp, max_tokens=mtoks)

    resp: Any
    try:
        if _router is not None:
            current_router = _router
            resp = await asyncio.to_thread(lambda: _call_router(current_router))
        else:
            resp = await asyncio.to_thread(_call_direct)
    except Exception as err:
        _router = None
        _logger.debug("litellm.router.disabled_after_failure")
        try:
            resp = await asyncio.to_thread(_call_direct)
        except Exception:
            alt_model = _choose_best_available_model(use_model)
            if alt_model != use_model:
                use_model = alt_model
                resp = await asyncio.to_thread(lambda: _litellm.completion(model=use_model, messages=messages, temperature=temp, max_tokens=mtoks))
            else:
                raise err from None

    content: str
    try:
        msg = resp.choices[0].message
        content = str(msg.get("content", "")) if isinstance(msg, dict) else str(getattr(msg, "content", ""))
    except Exception:
        content = str(getattr(resp, "content", ""))

    provider = getattr(resp, "provider", None)
    model_used = getattr(resp, "model", use_model)
    return LlmOutput(content=content or "", model=str(model_used), provider=str(provider) if provider else None)


def _bridge_provider_env() -> None:
    """Populate os.environ with provider API keys from .env via decouple if missing.

    Also map common synonyms to LiteLLM's canonical env names, e.g. GEMINI_API_KEY -> GOOGLE_API_KEY,
    GROK_API_KEY -> XAI_API_KEY.
    """
    from decouple import RepositoryEmpty

    try:
        cfg = DecoupleConfig(RepositoryEnv(".env"))
    except FileNotFoundError:
        cfg = DecoupleConfig(RepositoryEmpty())

    def _get_from_any(*keys: str) -> str:
        for k in keys:
            v = os.environ.get(k)
            if v:
                return v
        for k in keys:
            try:
                v = cfg(k, default="")
            except Exception:
                v = ""
            if v:
                return v
        return ""

    mappings: list[tuple[str, tuple[str, ...]]] = [
        ("OPENAI_API_KEY", ("OPENAI_API_KEY",)),
        ("ANTHROPIC_API_KEY", ("ANTHROPIC_API_KEY",)),
        ("GROQ_API_KEY", ("GROQ_API_KEY",)),
        ("XAI_API_KEY", ("XAI_API_KEY", "GROK_API_KEY")),
        ("GOOGLE_API_KEY", ("GOOGLE_API_KEY", "GEMINI_API_KEY")),
        ("OPENROUTER_API_KEY", ("OPENROUTER_API_KEY",)),
        ("DEEPSEEK_API_KEY", ("DEEPSEEK_API_KEY",)),
    ]

    for canonical, aliases in mappings:
        if not os.environ.get(canonical):
            val = _get_from_any(*aliases)
            if val:
                os.environ[canonical] = val
