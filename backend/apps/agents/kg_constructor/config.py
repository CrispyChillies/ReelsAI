"""
Configuration utilities for the Knowledge Graph Constructor.

This module provides helper functions to easily configure different LLM providers.
"""

import os
from typing import Optional


def get_openai_llm(
    model: str = "gpt-3.5-turbo",
    temperature: float = 0.0,
    api_key: Optional[str] = None
):
    """
    Get OpenAI LLM instance.
    
    Args:
        model: Model name (gpt-3.5-turbo, gpt-4, gpt-4-turbo, etc.)
        temperature: Temperature for generation (0.0 = deterministic)
        api_key: Optional API key (defaults to OPENAI_API_KEY env var)
    
    Returns:
        ChatOpenAI instance
    """
    try:
        from langchain_openai import ChatOpenAI
    except ImportError:
        raise ImportError(
            "langchain-openai not installed. "
            "Install with: pip install langchain-openai"
        )
    
    return ChatOpenAI(
        model=model,
        temperature=temperature,
        api_key=api_key or os.getenv("OPENAI_API_KEY")
    )


def get_anthropic_llm(
    model: str = "claude-3-sonnet-20240229",
    temperature: float = 0.0,
    api_key: Optional[str] = None
):
    """
    Get Anthropic Claude LLM instance.
    
    Args:
        model: Model name (claude-3-opus, claude-3-sonnet, claude-3-haiku)
        temperature: Temperature for generation (0.0 = deterministic)
        api_key: Optional API key (defaults to ANTHROPIC_API_KEY env var)
    
    Returns:
        ChatAnthropic instance
    """
    try:
        from langchain_anthropic import ChatAnthropic
    except ImportError:
        raise ImportError(
            "langchain-anthropic not installed. "
            "Install with: pip install langchain-anthropic"
        )
    
    return ChatAnthropic(
        model=model,
        temperature=temperature,
        api_key=api_key or os.getenv("ANTHROPIC_API_KEY")
    )


def get_google_llm(
    model: str = "gemini-pro",
    temperature: float = 0.0,
    api_key: Optional[str] = None
):
    """
    Get Google Gemini LLM instance.
    
    Args:
        model: Model name (gemini-pro, gemini-pro-vision, etc.)
        temperature: Temperature for generation (0.0 = deterministic)
        api_key: Optional API key (defaults to GOOGLE_API_KEY env var)
    
    Returns:
        ChatGoogleGenerativeAI instance
    """
    try:
        from langchain_google_genai import ChatGoogleGenerativeAI
    except ImportError:
        raise ImportError(
            "langchain-google-genai not installed. "
            "Install with: pip install langchain-google-genai"
        )
    
    return ChatGoogleGenerativeAI(
        model=model,
        temperature=temperature,
        google_api_key=api_key or os.getenv("GOOGLE_API_KEY")
    )


def get_ollama_llm(
    model: str = "llama2",
    temperature: float = 0.0,
    base_url: str = "http://localhost:11434"
):
    """
    Get local Ollama LLM instance.
    
    Args:
        model: Model name (llama2, mistral, phi, etc.)
        temperature: Temperature for generation (0.0 = deterministic)
        base_url: Ollama server URL
    
    Returns:
        ChatOllama instance
    """
    try:
        from langchain_ollama import ChatOllama
    except ImportError:
        raise ImportError(
            "langchain-ollama not installed. "
            "Install with: pip install langchain-ollama"
        )
    
    return ChatOllama(
        model=model,
        temperature=temperature,
        base_url=base_url
    )


def get_llm(
    provider: str = "openai",
    model: Optional[str] = None,
    temperature: float = 0.0,
    api_key: Optional[str] = None
):
    """
    Get LLM instance based on provider name.
    
    Args:
        provider: Provider name (openai, anthropic, google, ollama)
        model: Optional model name (uses provider default if not specified)
        temperature: Temperature for generation (0.0 = deterministic)
        api_key: Optional API key
    
    Returns:
        LLM instance
    
    Examples:
        >>> llm = get_llm("openai", "gpt-4")
        >>> llm = get_llm("anthropic", "claude-3-opus-20240229")
        >>> llm = get_llm("ollama", "llama2")
    """
    provider = provider.lower()
    
    if provider == "openai":
        model = model or "gpt-3.5-turbo"
        return get_openai_llm(model, temperature, api_key)
    
    elif provider == "anthropic":
        model = model or "claude-3-sonnet-20240229"
        return get_anthropic_llm(model, temperature, api_key)
    
    elif provider == "google":
        model = model or "gemini-pro"
        return get_google_llm(model, temperature, api_key)
    
    elif provider == "ollama":
        model = model or "llama2"
        return get_ollama_llm(model, temperature)
    
    else:
        raise ValueError(
            f"Unknown provider: {provider}. "
            f"Supported providers: openai, anthropic, google, ollama"
        )


# Preset configurations for common use cases
PRESETS = {
    "fast": {
        "provider": "openai",
        "model": "gpt-3.5-turbo",
        "temperature": 0.0,
        "description": "Fast and cost-effective (OpenAI GPT-3.5)"
    },
    "quality": {
        "provider": "openai",
        "model": "gpt-4",
        "temperature": 0.0,
        "description": "Highest quality (OpenAI GPT-4)"
    },
    "balanced": {
        "provider": "anthropic",
        "model": "claude-3-sonnet-20240229",
        "temperature": 0.0,
        "description": "Good balance of speed and quality (Claude 3 Sonnet)"
    },
    "free": {
        "provider": "google",
        "model": "gemini-pro",
        "temperature": 0.0,
        "description": "Free tier available (Google Gemini Pro)"
    },
    "local": {
        "provider": "ollama",
        "model": "llama2",
        "temperature": 0.0,
        "description": "Privacy-focused local model (Ollama Llama 2)"
    }
}


def get_preset_llm(preset: str = "fast"):
    """
    Get LLM using a preset configuration.
    
    Args:
        preset: Preset name (fast, quality, balanced, free, local)
    
    Returns:
        LLM instance
    
    Examples:
        >>> llm = get_preset_llm("fast")      # GPT-3.5-turbo
        >>> llm = get_preset_llm("quality")   # GPT-4
        >>> llm = get_preset_llm("local")     # Ollama Llama2
    """
    if preset not in PRESETS:
        available = ", ".join(PRESETS.keys())
        raise ValueError(
            f"Unknown preset: {preset}. "
            f"Available presets: {available}"
        )
    
    config = PRESETS[preset]
    return get_llm(
        provider=config["provider"],
        model=config["model"],
        temperature=config["temperature"]
    )


def list_presets():
    """
    List all available preset configurations.
    """
    print("Available LLM Presets:")
    print("=" * 60)
    for name, config in PRESETS.items():
        print(f"\n{name.upper()}")
        print(f"  Provider: {config['provider']}")
        print(f"  Model: {config['model']}")
        print(f"  Description: {config['description']}")
    print("=" * 60)


if __name__ == "__main__":
    # Display available presets
    list_presets()
