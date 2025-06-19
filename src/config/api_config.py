from ..utils.logger import logger
import os
from dotenv import load_dotenv

load_dotenv()

"""
외부 API 연동을 위한 설정 관리 모듈

이 모듈은 다양한 외부 서비스의 API 키와 엔드포인트를 관리합니다:
- 카카오맵 API (장소 검색, 길찾기)
- 네이버 검색 API (여행지 정보, 블로그)
- Google Maps API (대체 지도 서비스)
- 항공편 API (Amadeus 또는 Skyscanner)
- 숙박 API (Booking.com 등)
"""


# from typing import List, Dict, Optional # 사용되지 않으므로 주석 처리 또는 삭제


class APIConfig:
    """글로벌 API 키 및 기본 설정"""

    def __init__(self):
        # OpenAI API
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        if not self.openai_api_key:
            logger.warning("OPENAI_API_KEY가 설정되지 않았습니다.")

        # Kakao General Keys (OAuth or Admin)
        self.kakao_client_id = os.getenv("KAKAO_CLIENT_ID")  # OAuth용
        self.kakao_app_admin_key = os.getenv("KAKAO_APP_ADMIN_KEY")  # 일부 API용
        self.kakao_rest_api_key = os.getenv(
            "KAKAO_REST_API_KEY")  # 지도, 로컬 API용

        if not self.kakao_rest_api_key:
            logger.warning(
                "KAKAO_REST_API_KEY가 없습니다. 지도/로컬 API 사용에 문제 발생 가능"
            )
        if not self.kakao_client_id:
            logger.warning(
                "KAKAO_CLIENT_ID가 없습니다. 사용자 인증 카카오 API 사용에 문제 발생 가능"
            )

        # Naver API (선택사항)
        self.naver_client_id = os.getenv("NAVER_CLIENT_ID")
        self.naver_client_secret = os.getenv("NAVER_CLIENT_SECRET")

        # 기타 API 키들...
        self.amadeus_api_key = os.getenv("AMADEUS_API_KEY")
        self.amadeus_api_secret = os.getenv("AMADEUS_API_SECRET")
        self.booking_api_key = os.getenv("BOOKING_API_KEY")


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
