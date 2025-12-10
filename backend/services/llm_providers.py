"""
LLM Provider Client

Provides interface to OpenAI and Gemini APIs for AI processing
"""

import json
import logging
from typing import Optional, Dict, Any, Union

import openai
import google.generativeai as genai

from app.config import settings

logger = logging.getLogger(__name__)


class GeminiProvider:
    """Google Gemini provider"""

    def __init__(self, api_key: str, model: str = "gemini-1.5-flash"):
        genai.configure(api_key=api_key)
        self.model_name = model
        self.model = genai.GenerativeModel(model)

    def generate(
        self,
        prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 1000,
        json_mode: bool = False
    ) -> str:
        """
        Generate text using Gemini API

        Args:
            prompt: The prompt text
            temperature: Sampling temperature (0-1 for Gemini)
            max_tokens: Maximum tokens to generate
            json_mode: Whether to enforce JSON output

        Returns:
            Generated text
        """
        try:
            # Gemini temperature is 0.0 - 1.0 (sometimes up to 2.0 depending on model, but 1.0 is safe)
            # OpenAI uses 0-2. We might need to normalize if passed high values, but 0.7 is safe for both.
            
            generation_config = genai.types.GenerationConfig(
                temperature=temperature,
                max_output_tokens=max_tokens,
            )
            
            if json_mode:
                generation_config.response_mime_type = "application/json"

            response = self.model.generate_content(
                prompt,
                generation_config=generation_config
            )
            
            result = response.text
            logger.info(f"Gemini API call successful - Model: {self.model_name}")

            return result

        except Exception as e:
            logger.error(f"Gemini API error: {str(e)}")
            raise

    def get_provider_name(self) -> str:
        return f"gemini-{self.model_name}"


class OpenAIProvider:
    """OpenAI GPT provider"""

    def __init__(self, api_key: str, model: str = "gpt-4-turbo-preview"):
        self.client = openai.OpenAI(api_key=api_key)
        self.model = model

    def generate(
        self,
        prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 1000,
        json_mode: bool = False
    ) -> str:
        """
        Generate text using OpenAI API

        Args:
            prompt: The prompt text
            temperature: Sampling temperature (0-2)
            max_tokens: Maximum tokens to generate
            json_mode: Whether to enforce JSON output

        Returns:
            Generated text
        """
        try:
            messages = [{"role": "user", "content": prompt}]

            # Build request parameters
            params = {
                "model": self.model,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens,
            }

            # Add JSON mode if requested (GPT-4 Turbo supports this)
            if json_mode and "gpt-4" in self.model:
                params["response_format"] = {"type": "json_object"}

            response = self.client.chat.completions.create(**params)

            result = response.choices[0].message.content
            logger.info(f"OpenAI API call successful - Model: {self.model}")

            return result

        except Exception as e:
            logger.error(f"OpenAI API error: {str(e)}")
            raise

    def get_provider_name(self) -> str:
        return f"openai-{self.model}"


def get_llm_provider(model: Optional[str] = None) -> Union[OpenAIProvider, GeminiProvider]:
    """
    Get LLM provider instance based on configuration

    Args:
        model: Model name. If None, uses default from settings

    Returns:
        Provider instance (OpenAIProvider or GeminiProvider)

    Raises:
        ValueError: If API key is missing
    """
    provider_type = settings.DEFAULT_LLM_PROVIDER.lower()

    if provider_type == "gemini":
        if not settings.GEMINI_API_KEY:
            raise ValueError("Gemini API key not configured")
        
        model = model or settings.DEFAULT_LLM_MODEL
        # If model is still default OpenAI model, switch to Gemini default
        if model == "gpt-4-turbo-preview":
            model = "gemini-1.5-flash"
            
        return GeminiProvider(api_key=settings.GEMINI_API_KEY, model=model)

    # Default to OpenAI
    if not settings.OPENAI_API_KEY:
        # Fallback to Gemini if OpenAI is missing but Gemini is present
        if settings.GEMINI_API_KEY:
            model = model or "gemini-1.5-flash"
            return GeminiProvider(api_key=settings.GEMINI_API_KEY, model=model)
        raise ValueError("OpenAI API key not configured")

    model = model or settings.OPENAI_MODEL
    return OpenAIProvider(api_key=settings.OPENAI_API_KEY, model=model)


def parse_json_response(response: str) -> Dict[str, Any]:
    """
    Parse JSON response from LLM

    Handles cases where LLM includes markdown code blocks or extra text

    Args:
        response: Raw LLM response

    Returns:
        Parsed JSON as dictionary

    Raises:
        ValueError: If response is not valid JSON
    """
    try:
        # Try direct parsing first
        return json.loads(response)
    except json.JSONDecodeError:
        # Try to extract JSON from markdown code blocks
        if "```json" in response:
            start = response.find("```json") + 7
            end = response.find("```", start)
            json_str = response[start:end].strip()
            return json.loads(json_str)
        elif "```" in response:
            start = response.find("```") + 3
            end = response.find("```", start)
            json_str = response[start:end].strip()
            return json.loads(json_str)
        else:
            # Try to find JSON object in text
            start = response.find("{")
            end = response.rfind("}") + 1
            if start != -1 and end != 0:
                json_str = response[start:end]
                return json.loads(json_str)

        raise ValueError(f"Could not parse JSON from response: {response[:200]}")
