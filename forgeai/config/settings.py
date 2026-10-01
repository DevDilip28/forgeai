import os

from dotenv import load_dotenv

load_dotenv()


class Settings:
    def __init__(self):
        self.groq_api_key = os.getenv("GROQ_API_KEY")
        self.model_name = os.getenv(
            "MODEL_NAME",
            "openai/gpt-oss-20b",
        )
        self.temperature = float(os.getenv("TEMPERATURE", "0.7"))
        self.max_tokens = int(os.getenv("MAX_TOKENS", "4096"))

        if not self.groq_api_key:
            raise ValueError("GROQ_API_KEY is not set in the .env file.")


settings = Settings()
