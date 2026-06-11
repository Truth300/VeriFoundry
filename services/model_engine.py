import os
from openai import OpenAI
from azure.identity import DefaultAzureCredential, get_bearer_token_provider

# Global execution configurations required by main.py
MODEL_EXECUTION_OPTIONS = {
    "default": {
        "temperature": 0.0,
        "max_tokens": 4096,
        "top_p": 1.0
    },
    "gpt-4.1-mini": {
        "temperature": 0.0,
        "max_tokens": 4096,
        "top_p": 1.0
    }
}

class ModelEngine:
    def __init__(self):
        # 1. Grab configurations from environment variables
        self.endpoint = os.getenv("AZURE_OPENAI_ENDPOINT", "https://verifoundry1-resource.services.ai.azure.com/openai/v1")
        self.deployment_name = os.getenv("AZURE_DEPLOYMENT_NAME", "gpt-4.1-mini")
        
        # 2. Build the secure Azure bearer token provider
        token_provider = get_bearer_token_provider(
            DefaultAzureCredential(), 
            "https://ai.azure.com/.default"
        )
        
        # 3. Initialize the OpenAI client pointing to the Azure infrastructure
        self.client = OpenAI(
            base_url=self.endpoint,
            api_key=token_provider
        )

    async def call_llm(self, system_prompt: str, user_prompt: str) -> str:
        """Executes a chat completion against your deployed gpt-4.1-mini model."""
        try:
            completion = self.client.chat.completions.create(
                model=self.deployment_name,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=MODEL_EXECUTION_OPTIONS["gpt-4.1-mini"]["temperature"]
            )
            return completion.choices[0].message.content
        except Exception as e:
            raise RuntimeError(f"Azure OpenAI Inference Error: {e}")