"""
Application configuration settings.
"""
import os

from dotenv import load_dotenv

# .env 파일에서 환경 변수 로드
load_dotenv()


class Settings:
    """어플리케이션 세팅"""

    def __init__(self):
        # OpenAI API
        self.openai_api_key = os.getenv("OPENAI_API_KEY", "")
        self.openai_model = os.getenv("OPENAI_MODEL", "gpt-4o")
        self.openai_temperature = float(os.getenv("OPENAI_TEMPERATURE", "0.7"))
        self.max_tokens = int(os.getenv("MAX_TOKENS", "1000"))

        # External API Keys
        self.kakao_rest_api_key = os.getenv("KAKAO_REST_API_KEY")
        self.kakao_refresh_token = os.getenv("KAKAO_REFRESH_TOKEN")

        self.google_search_api_key = os.getenv("GOOGLE_SEARCH_API_KEY")
        self.google_search_cx = os.getenv("GOOGLE_SEARCH_CX")

        # Application Settings
        self.debug = os.getenv("DEBUG", "False").lower() == "true"
        self.log_level = os.getenv("LOG_LEVEL", "INFO")

        # Streamlit Settings
        self.page_title = "🌍 여행 플래너 AI"
        self.page_icon = "🌍"


# Global settings instance
settings = Settings()
