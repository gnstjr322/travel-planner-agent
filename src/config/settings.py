"""
Application configuration settings.
"""
import os


class Settings:
    """Application settings."""

    def __init__(self):
        # OpenAI API
        self.openai_api_key = os.getenv("OPENAI_API_KEY", "")
        self.openai_model = os.getenv("OPENAI_MODEL", "gpt-4-turbo-preview")
        self.openai_temperature = float(os.getenv("OPENAI_TEMPERATURE", "0.7"))
        self.max_tokens = int(os.getenv("MAX_TOKENS", "1000"))

        # External API Keys
        self.kakao_rest_api_key = os.getenv("KAKAO_REST_API_KEY")
        self.naver_client_id = os.getenv("NAVER_CLIENT_ID")
        self.naver_client_secret = os.getenv("NAVER_CLIENT_SECRET")

        # Google Calendar API (이제 사용하지 않으므로 삭제)
        # self.google_client_id = os.getenv("GOOGLE_CLIENT_ID")
        # self.google_client_secret = os.getenv("GOOGLE_CLIENT_SECRET")

        # Application Settings
        self.debug = os.getenv("DEBUG", "False").lower() == "true"
        self.log_level = os.getenv("LOG_LEVEL", "INFO")

        # Streamlit Settings
        self.page_title = "🌍 여행 플래너 AI"
        self.page_icon = "🌍"


# Global settings instance
settings = Settings()
