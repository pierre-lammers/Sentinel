"""LLM Provider Factory for centralizing LLM instantiation and configuration."""

from __future__ import annotations

import os
from enum import Enum
from typing import Any

from langchain.agents import create_agent
from langchain.agents.middleware import ModelRetryMiddleware
from langchain_core.language_models import BaseChatModel
from langchain_mistralai import ChatMistralAI
from mistralai import Mistral
from pydantic import SecretStr


class LLMProvider(str, Enum):
    """Supported LLM providers."""

    MISTRAL = "mistral"
    OPENAI = "openai"
    ANTHROPIC = "anthropic"


class LLMConfig:
    """Configuration for LLM factory.

    This centralizes all LLM-related configuration in one place.
    To change the default provider or model, modify the values here.
    """

    # Default provider (can be overridden by LLM_PROVIDER env var)
    DEFAULT_PROVIDER: LLMProvider = LLMProvider.MISTRAL

    # Default models per provider
    DEFAULT_MODELS = {
        LLMProvider.MISTRAL: "codestral-2501",
        LLMProvider.OPENAI: "gpt-4",
        LLMProvider.ANTHROPIC: "claude-3-5-sonnet-20241022",
    }

    # Default temperature
    DEFAULT_TEMPERATURE: float = 0.0

    # Retry configuration (following ModelRetryMiddleware pattern)
    DEFAULT_MAX_RETRIES: int = 3
    DEFAULT_BACKOFF_FACTOR: float = 2.0
    DEFAULT_INITIAL_DELAY: float = 1.0

    @classmethod
    def get_provider(cls) -> LLMProvider:
        """Get the configured provider from environment or default."""
        provider_str = os.getenv("LLM_PROVIDER", cls.DEFAULT_PROVIDER.value).lower()
        try:
            return LLMProvider(provider_str)
        except ValueError:
            return cls.DEFAULT_PROVIDER

    @classmethod
    def get_default_model(cls, provider: LLMProvider | None = None) -> str:
        """Get the default model for the given provider."""
        if provider is None:
            provider = cls.get_provider()
        return cls.DEFAULT_MODELS.get(
            provider, cls.DEFAULT_MODELS[cls.DEFAULT_PROVIDER]
        )


def get_llm(
    model: str | None = None,
    temperature: float | None = None,
    provider: LLMProvider | None = None,
) -> BaseChatModel:
    """Get a LangChain LLM instance configured with the specified provider.

    This is the main factory function for getting LLM instances.
    It supports multiple providers and can be easily extended.

    Args:
        model: Model name to use. If None, uses the default for the provider.
        temperature: Temperature for the model. If None, uses DEFAULT_TEMPERATURE.
        provider: LLM provider to use. If None, uses the configured default.

    Returns:
        A configured LangChain BaseChatModel instance.

    Raises:
        ValueError: If required API keys are not set or provider is not supported.

    Example:
        # Use default provider and model
        llm = get_llm()

        # Use specific model with default provider
        llm = get_llm(model="codestral-2501")

        # Use different provider
        llm = get_llm(provider=LLMProvider.OPENAI, model="gpt-4")
    """
    if provider is None:
        provider = LLMConfig.get_provider()

    if model is None:
        model = LLMConfig.get_default_model(provider)

    if temperature is None:
        temperature = LLMConfig.DEFAULT_TEMPERATURE

    if provider == LLMProvider.MISTRAL:
        return _get_mistral_llm(model=model, temperature=temperature)
    elif provider == LLMProvider.OPENAI:
        return _get_openai_llm(model=model, temperature=temperature)
    elif provider == LLMProvider.ANTHROPIC:
        return _get_anthropic_llm(model=model, temperature=temperature)
    else:
        raise ValueError(f"Unsupported provider: {provider}")


def _get_mistral_llm(model: str, temperature: float) -> ChatMistralAI:
    """Get a ChatMistralAI instance configured with API key.

    Args:
        model: Model name to use.
        temperature: Temperature for the model.

    Returns:
        Configured ChatMistralAI instance.

    Raises:
        ValueError: If MISTRAL_API_KEY is not set.
    """
    api_key = os.getenv("MISTRAL_API_KEY")
    if not api_key:
        raise ValueError("MISTRAL_API_KEY not set")
    return ChatMistralAI(
        model_name=model,
        temperature=temperature,
        api_key=SecretStr(api_key),
    )


def _get_openai_llm(model: str, temperature: float) -> BaseChatModel:
    """Get a ChatOpenAI instance configured with API key.

    Args:
        model: Model name to use.
        temperature: Temperature for the model.

    Returns:
        Configured ChatOpenAI instance.

    Raises:
        ValueError: If OPENAI_API_KEY is not set.
        ImportError: If langchain-openai is not installed.
    """
    try:
        from langchain_openai import ChatOpenAI
    except ImportError as e:
        raise ImportError(
            "langchain-openai is not installed. "
            "Install it with: pip install langchain-openai"
        ) from e

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY not set")

    return ChatOpenAI(
        model=model,
        temperature=temperature,
        api_key=SecretStr(api_key),
    )


def _get_anthropic_llm(model: str, temperature: float) -> BaseChatModel:
    """Get a ChatAnthropic instance configured with API key.

    Args:
        model: Model name to use.
        temperature: Temperature for the model.

    Returns:
        Configured ChatAnthropic instance.

    Raises:
        ValueError: If ANTHROPIC_API_KEY is not set.
        ImportError: If langchain-anthropic is not installed.
    """
    try:
        from langchain_anthropic import ChatAnthropic
    except ImportError as e:
        raise ImportError(
            "langchain-anthropic is not installed. "
            "Install it with: pip install langchain-anthropic"
        ) from e

    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY not set")

    return ChatAnthropic(  # type: ignore[call-arg]
        model_name=model,
        temperature=temperature,
        api_key=SecretStr(api_key),
    )


def get_mistral_client() -> Mistral:
    """Get a Mistral SDK client instance.

    This is for direct Mistral SDK usage (not LangChain).
    Used for structured output parsing with response_format.

    Returns:
        Configured Mistral client instance.

    Raises:
        ValueError: If MISTRAL_API_KEY is not set.
    """
    api_key = os.getenv("MISTRAL_API_KEY")
    if not api_key:
        raise ValueError("MISTRAL_API_KEY not set")
    return Mistral(api_key=api_key)


def get_retry_middleware(
    max_retries: int | None = None,
    backoff_factor: float | None = None,
    initial_delay: float | None = None,
) -> ModelRetryMiddleware:
    """Create retry middleware with exponential backoff.

    Args:
        max_retries: Maximum number of retry attempts
        backoff_factor: Exponential backoff multiplier
        initial_delay: Initial delay in seconds before first retry

    Returns:
        Configured ModelRetryMiddleware instance
    """
    if max_retries is None:
        max_retries = LLMConfig.DEFAULT_MAX_RETRIES
    if backoff_factor is None:
        backoff_factor = LLMConfig.DEFAULT_BACKOFF_FACTOR
    if initial_delay is None:
        initial_delay = LLMConfig.DEFAULT_INITIAL_DELAY

    return ModelRetryMiddleware(
        max_retries=max_retries,
        backoff_factor=backoff_factor,
        initial_delay=initial_delay,
    )


def get_agent(
    model: str | None = None,
    temperature: float | None = None,
    provider: LLMProvider | None = None,
    tools: list[Any] | None = None,
    response_format: Any | None = None,
    system_prompt: str | None = None,
    max_retries: int | None = None,
    backoff_factor: float | None = None,
    initial_delay: float | None = None,
    additional_middleware: list[Any] | None = None,
) -> Any:
    """Create a LangChain agent with retry middleware and optional tools.

    Args:
        model: Model name/ID to use
        temperature: Model temperature for generation
        provider: LLM provider to use
        tools: List of tools to provide to the agent
        response_format: Structured output format
        system_prompt: System prompt for the agent
        max_retries: Maximum number of retry attempts
        backoff_factor: Exponential backoff multiplier
        initial_delay: Initial delay in seconds before first retry
        additional_middleware: Additional middleware to apply

    Returns:
        Configured agent instance
    """
    # Get the base LLM instance
    llm = get_llm(model=model, temperature=temperature, provider=provider)

    # Create the retry middleware using the dedicated function
    retry_middleware = get_retry_middleware(
        max_retries=max_retries,
        backoff_factor=backoff_factor,
        initial_delay=initial_delay,
    )

    # Combine retry middleware with additional middleware
    middleware = [retry_middleware]
    if additional_middleware:
        middleware.extend(additional_middleware)

    # Create the agent with all middleware
    agent = create_agent(
        model=llm,
        tools=tools or [],
        middleware=middleware,
        response_format=response_format,
        system_prompt=system_prompt,
    )

    return agent
