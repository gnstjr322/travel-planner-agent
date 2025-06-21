import os

from dotenv import load_dotenv

from ..utils.logger import logger

load_dotenv()

"""
외부 API 연동을 위한 설정 관리 모듈

이 모듈은 다양한 외부 서비스의 API 키와 엔드포인트를 관리합니다:
- 카카오맵 API (장소 검색, 길찾기)
- Google Maps API (대체 지도 서비스)
"""


class APIConfig:
    """글로벌 API 키 및 기본 설정"""

    def __init__(self):
        # OpenAI API
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        if not self.openai_api_key:
            logger.warning("OPENAI_API_KEY가 설정되지 않았습니다.")

        # Kakao General Keys (OAuth or Admin)
        self.kakao_rest_api_key = os.getenv(
            "KAKAO_REST_API_KEY")  # 지도, 로컬 API용

        if not self.kakao_rest_api_key:
            logger.warning(
                "KAKAO_REST_API_KEY가 없습니다. 지도/로컬 API 사용에 문제 발생 가능"
            )

        self.tavily_api_key = os.getenv(
            "TAVILY_API_KEY")  # 웹 검색 API용

        if not self.tavily_api_key:
            logger.warning(
                "TAVILY_API_KEY가 없습니다. 웹 검색 API 사용에 문제 발생 가능"
            )

        self.notion_api_key = os.getenv(
            "NOTION_API_KEY")  # 노션 API용

        if not self.notion_api_key:
            logger.warning(
                "NOTION_API_KEY가 없습니다. 노션 API 사용에 문제 발생 가능"
            )


# 전역 API 설정 인스턴스
api_config = APIConfig()


class KakaoCalendarConfig:
    """KakaoTalk Calendar API 특정 설정"""

    def __init__(self):
        self.api_base_url = "https://kapi.kakao.com"  # 카카오 API 서버
        self.auth_base_url = "https://kauth.kakao.com"  # 카카오 인증 서버
        self.default_calendar_id = "primary"
        self.scopes = ["talk_calendar"]  # 톡캘린더 권한
        self.timezone = os.getenv("APP_TIMEZONE", "Asia/Seoul")


class KakaoMapConfig:
    """KakaoMap API 특정 설정"""

    def __init__(self):
        # 지도 API는 주로 REST API 키 사용
        self.rest_api_key = api_config.kakao_rest_api_key
        self.api_base_url = "https://dapi.kakao.com"


class DuckDuckGoConfig:
    """DuckDuckGo Search API 설정"""
    pass  # 특별한 설정 없음


# 전역 설정 인스턴스 생성
kakao_calendar_config = KakaoCalendarConfig()
kakao_map_config = KakaoMapConfig()
duckduckgo_config = DuckDuckGoConfig()
