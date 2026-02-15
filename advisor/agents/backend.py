"""
BeeAI Framework Backend Configuration.

This module configures the LLM backend for BeeAI agents.
"""

from typing import Optional
from loguru import logger
from beeai_framework.backend.chat import ChatModel
from beeai_framework.backend.chat import ChatModelParameters

# Use the creation method directly if available, or just generic init
# Inspection showed `ChatModel` class. Let's see if we can instantiate it with provider config.

class BeeAIBackend:
    """Backend factory for BeeAI."""

    @staticmethod
    def get_chat_model(model_name: str, temperature: float = 0.7) -> Optional[ChatModel]:
        """
        Get a configured ChatModel for Ollama.
        Uses the OpenAI provider interface which is compatible with Ollama.
        """
        try:
            # We will use ChatModel.from_name with specific provider syntax if possible
            # or manual instantiation.
            # "openai/model_name" often works if we set base_url.

            # However, looking at BeeAI source patterns (from general knowledge of similar frameworks),
            # one often needs to import the specific provider class.

            # Since we can't easily see the provider submodules (failed inspection earlier didn't show them deeply),
            # let's try a standard "openai" provider string which `from_name` might handle via LiteLLM.
            # But we need to set the API base.

            # Let's try to set the environment variable for LiteLLM/OpenAI to point to Ollama
            # inside here before creating the model.
            import os
            os.environ["OPENAI_API_BASE"] = "http://localhost:11434/v1"
            os.environ["OPENAI_API_KEY"] = "ollama" # Dummy key

            # Now try loading with 'openai/modelname' which LiteLLM supports and BeeAI likely uses.
            # Ollama model names need to be passed as is, e.g. "llama3.1:8b"

            model = ChatModel.from_name(f"openai/{model_name}")
            return model

        except Exception as e:
            logger.error(f"Failed to load model via OpenAI/LiteLLM bridge: {e}")
            return None
