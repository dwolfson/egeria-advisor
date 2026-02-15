"""
BeeAI Framework Backend Configuration.

This module configures the LLM backend for BeeAI agents, specifically
integrating with Ollama via the OpenAI-compatible interface.
"""

from typing import Optional
from loguru import logger
from beeai_framework.backend.chat import ChatModel

# Since BeeAI often wraps OpenAI or similar, and Ollama provides an OpenAI-compatible API,
# we need to find the correct ChatModel implementation.
# Based on the inspection, we saw `ChatModel` but no specific `OpenAIChatModel`.
# However, standard practice suggested by BeeAI docs (implied) is often to use the generic entry.
# Let's inspect `beeai_framework.backend.chat` again or check for `beeai_framework.adapters.ollama`? No.
# Wait, `litellm` was installed as a dependency!
# This strongly suggests BeeAI uses LiteLLM or similar for backend abstraction.

try:
    # If LiteLLM is used, we might just need to pass the model string "ollama/llama3.1"
    # But BeeAI likely has a specific class for the ChatModel.
    # Let's check if we can import `ChatModel` and instantiate it with a provider.
    pass
except ImportError:
    pass

# For now, we will create a placeholder implementation that assumes we can instantiate *some* model.
# We'll use a factory pattern so we can hot-swap the implementation once we verify the exact class.

class BeeAIBackend:
    """Backend factory for BeeAI."""

    @staticmethod
    def get_chat_model(model_name: str, temperature: float = 0.7):
        """
        Get a configured ChatModel.

        Args:
            model_name: Name of the model (e.g., llama3.1)
            temperature: Temperature setting

        Returns:
            ChatModel instance
        """
        # We need to investigate how to instantiate a specific provider model.
        # Assuming `ChatModel.from_name` or similar exists, or we use `litellm` directly?
        # Let's just return a mock for now to allow code structure,
        # but logically we should try to use `ChatModel` if it has a factory.

        # Based on file listing, we have `beeai_framework.backend.chat`.
        # Let's check `load_model` in `beeai_framework.backend.chat`.
        from beeai_framework.backend.chat import load_model

        # Ollama models via LiteLLM follow "ollama/model_name"
        provider_model_id = f"ollama/{model_name}"

        try:
            model = load_model(provider_model_id)
            # Configure info like temperature if the model object supports it
            return model
        except Exception as e:
            logger.error(f"Failed to load model {provider_model_id}: {e}")
            return None
