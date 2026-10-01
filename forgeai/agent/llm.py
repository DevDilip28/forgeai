from groq import Groq

from forgeai.config.settings import settings


class LLMClient:
    def __init__(self):
        self.client = Groq(api_key=settings.groq_api_key)

    def generate_response(self, user_message: str) -> str:
        response = self.client.chat.completions.create(
            model=settings.model_name,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are ForgeAI, an AI coding assistant. "
                        "Be helpful, clear, and concise."
                    ),
                },
                {
                    "role": "user",
                    "content": user_message,
                },
            ],
            temperature=settings.temperature,
            max_tokens=settings.max_tokens,
        )

        return response.choices[0].message.content or ""


llm_client = LLMClient()
