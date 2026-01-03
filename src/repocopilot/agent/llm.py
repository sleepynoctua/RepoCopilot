import os
import json
from typing import Dict, Any, Optional
from openai import OpenAI
from .prompt import SUFFICIENCY_PROMPT


class LLMClient:
    def __init__(
        self,
        model: str = None,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
    ):
        self.client = OpenAI(
            api_key=api_key or os.getenv("OPENAI_API_KEY"),
            base_url=base_url or os.getenv("OPENAI_API_BASE"),
        )
        # Priority: constructor argument > environment variable > raise error
        self.model = model or os.getenv("MODEL_NAME")
        if not self.model:
            raise ValueError("MODEL_NAME is not set. Please check your .env file.")

    def chat(self, messages: list) -> str:
        """
        Standard chat completion.
        """
        response = self.client.chat.completions.create(
            model=self.model, messages=messages, temperature=0.0
        )
        return response.choices[0].message.content

    def evaluate_sufficiency(self, query: str, context: str) -> Dict[str, Any]:
        """
        Check if the retrieved context is sufficient to answer the query.
        Returns a JSON object.
        """
        prompt = SUFFICIENCY_PROMPT.format(query=query, context=context)

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {
                    "role": "system",
                    "content": "You are a helpful assistant that outputs JSON.",
                },
                {"role": "user", "content": prompt},
            ],
            response_format={"type": "json_object"},
            temperature=0.0,
        )

        try:
            return json.loads(response.choices[0].message.content)
        except json.JSONDecodeError:
            # Fallback if JSON parsing fails
            return {
                "sufficient": False,
                "missing_info": "Failed to parse LLM response",
                "suggested_query": query,
            }
