"""
LLM client wrapper for Ollama integration.

This module provides a simple interface to interact with Ollama models
for text generation with the Egeria Advisor.
"""

import requests
from typing import Optional, Dict, Any, List
from loguru import logger
import json

from advisor.config import settings, get_full_config


class OllamaClient:
    """Client for interacting with Ollama LLM API."""
    
    def __init__(
        self,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
        timeout: int = 60
    ):
        """
        Initialize Ollama client.
        
        Args:
            base_url: Ollama API base URL
            model: Default model to use
            timeout: Request timeout in seconds
        """
        config = get_full_config()
        llm_config = config.get("llm")
        
        self.base_url = base_url or llm_config.base_url
        self.default_model = model or llm_config.models.query
        self.timeout = timeout or llm_config.parameters.timeout
        
        # Get default parameters
        self.default_params = {
            "temperature": llm_config.parameters.temperature,
            "top_p": llm_config.parameters.top_p,
            "top_k": llm_config.parameters.top_k,
            "repeat_penalty": llm_config.parameters.repeat_penalty
        }
        
        logger.info(f"Initialized Ollama client: {self.base_url}")
        logger.info(f"Default model: {self.default_model}")
    
    def is_available(self) -> bool:
        """Check if Ollama service is available."""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            return response.status_code == 200
        except Exception as e:
            logger.warning(f"Ollama not available: {e}")
            return False
    
    def list_models(self) -> List[str]:
        """List available models."""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            response.raise_for_status()
            data = response.json()
            models = [model["name"] for model in data.get("models", [])]
            logger.info(f"Available models: {models}")
            return models
        except Exception as e:
            logger.error(f"Failed to list models: {e}")
            return []
    
    def generate(
        self,
        prompt: str,
        model: Optional[str] = None,
        system: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        stream: bool = False,
        **kwargs
    ) -> str:
        """
        Generate text completion.
        
        Args:
            prompt: Input prompt
            model: Model to use (defaults to configured model)
            system: System prompt
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            stream: Whether to stream the response
            **kwargs: Additional parameters
            
        Returns:
            Generated text
        """
        model = model or self.default_model
        
        # Build request payload
        payload = {
            "model": model,
            "prompt": prompt,
            "stream": stream,
            "options": {
                "temperature": temperature or self.default_params["temperature"],
                "top_p": self.default_params["top_p"],
                "top_k": self.default_params["top_k"],
                "repeat_penalty": self.default_params["repeat_penalty"]
            }
        }
        
        if system:
            payload["system"] = system
        
        if max_tokens:
            payload["options"]["num_predict"] = max_tokens
        
        # Add any additional options
        payload["options"].update(kwargs)
        
        logger.debug(f"Generating with model: {model}")
        logger.debug(f"Prompt length: {len(prompt)} chars")
        
        try:
            response = requests.post(
                f"{self.base_url}/api/generate",
                json=payload,
                timeout=self.timeout
            )
            response.raise_for_status()
            
            if stream:
                # Handle streaming response
                full_response = ""
                for line in response.iter_lines():
                    if line:
                        data = json.loads(line)
                        if "response" in data:
                            full_response += data["response"]
                return full_response
            else:
                # Handle non-streaming response
                data = response.json()
                generated_text = data.get("response", "")
                
                logger.debug(f"Generated {len(generated_text)} chars")
                return generated_text
                
        except requests.exceptions.Timeout:
            logger.error(f"Request timed out after {self.timeout}s")
            raise
        except Exception as e:
            logger.error(f"Generation failed: {e}")
            raise
    
    def chat(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        stream: bool = False,
        **kwargs
    ) -> str:
        """
        Chat completion with message history.
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            model: Model to use
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            stream: Whether to stream the response
            **kwargs: Additional parameters
            
        Returns:
            Generated response
        """
        model = model or self.default_model
        
        payload = {
            "model": model,
            "messages": messages,
            "stream": stream,
            "options": {
                "temperature": temperature or self.default_params["temperature"],
                "top_p": self.default_params["top_p"],
                "top_k": self.default_params["top_k"],
                "repeat_penalty": self.default_params["repeat_penalty"]
            }
        }
        
        if max_tokens:
            payload["options"]["num_predict"] = max_tokens
        
        payload["options"].update(kwargs)
        
        logger.debug(f"Chat with {len(messages)} messages")
        
        try:
            response = requests.post(
                f"{self.base_url}/api/chat",
                json=payload,
                timeout=self.timeout
            )
            response.raise_for_status()
            
            if stream:
                full_response = ""
                for line in response.iter_lines():
                    if line:
                        data = json.loads(line)
                        if "message" in data and "content" in data["message"]:
                            full_response += data["message"]["content"]
                return full_response
            else:
                data = response.json()
                message = data.get("message", {})
                return message.get("content", "")
                
        except Exception as e:
            logger.error(f"Chat failed: {e}")
            raise


# Global client instance
_ollama_client: Optional[OllamaClient] = None


def get_ollama_client() -> OllamaClient:
    """Get or create the global Ollama client instance."""
    global _ollama_client
    
    if _ollama_client is None:
        _ollama_client = OllamaClient()
    
    return _ollama_client