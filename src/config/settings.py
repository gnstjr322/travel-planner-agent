"""
Settings and configuration management for the Travel Planner Agent.
"""
import os
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from pydantic_settings import BaseSettings

# .env 파일에서 환경 변수 로드
load_dotenv()


class Settings(BaseSettings):
    """어플리케이션 세팅"""

    # OpenAI API
    openai_api_key: str = ""
    openai_model: str = "gpt-4o"
    openai_temperature: float = 0.7
    max_tokens: int = 1000

    # Kakao API
    kakao_rest_api_key: str = ""
    kakao_auth_code: str = ""
    kakao_access_token: str = ""
    kakao_refresh_token: str = ""

    # Google Search API
    google_search_api_key: str = ""
    google_search_cx: str = ""

    # Tavily API
    tavily_api_key: str = ""

    # Notion API
    notion_api_key: str = ""
    notion_database_id: str = ""

    # Application Configuration
    app_name: str = "Travel Planner Multi-Agent"
    app_version: str = "1.0.0"
    debug: bool = True
    log_level: str = "INFO"

    # Multi-Agent System Settings
    default_model: str = "gpt-4o-mini"
    agent_temperature: float = 0.0
    max_search_results: int = 5
    search_timeout: int = 10

    # Streamlit UI Configuration
    page_title: str = "🌍 AI 여행 플래너"
    page_icon: str = "🌍"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


# Global settings instance
settings = Settings()
