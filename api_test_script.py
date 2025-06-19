import asyncio
import json
from datetime import datetime, timedelta

from dotenv import load_dotenv

from src.services.duckduckgo_service import DuckDuckGoService
from src.services.kakao_calendar_service import KakaoCalendarService
from src.services.kakao_service import KakaoMapService

# 스크립트 시작 시 .env 파일 로드
load_dotenv()

# 서비스 클래스 임포트


def print_header(title):
    """테스트 섹션 헤더를 출력합니다."""
    print("\n" + "=" * 50)
    print(f"🔄 {title}")
    print("=" * 50)


def print_result(result):
    """결과를 JSON 형식으로 예쁘게 출력합니다."""
    try:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    except TypeError:
        print(str(result))  # JSON 직렬화 실패 시 문자열로 출력
    print("-" * 20)


async def test_kakao_map_api():
    """카카오맵 API를 테스트합니다."""
    print_header("카카오맵 API 테스트")
    try:
        service = KakaoMapService()
        if not service.api_key:
            print("❌ 카카오맵 API 키가 없어 테스트를 건너뜁니다.")
            return
        # 'limit' 인자를 사용하여 호출
        places = await service.search_places("서울시청 맛집", limit=3)
        print_result(places)
    except Exception as e:
        print(f"❌ 오류 발생: {e}")


async def test_duckduckgo_search_api():
    """DuckDuckGo 웹 검색 API를 테스트합니다."""
    print_header("웹 검색 (DuckDuckGo) API 테스트")
    try:
        service = DuckDuckGoService()
        # 'safesearch' 인자를 포함하여 호출
        results = await service.search_web(
            query="오늘의 주요 뉴스", max_results=3, safesearch="moderate"
        )
        print_result(results)
    except Exception as e:
        print(f"❌ 오류 발생: {e}")


async def test_kakao_calendar_api():
    """카카오톡 캘린더 API를 테스트합니다."""
    print_header("카카오톡 캘린더 API 테스트")
    try:
        service = KakaoCalendarService()
        if not service.access_token:
            # 헤더 생성 시점에 토큰을 로드하므로, 여기서 미리 호출해봄
            try:
                service._get_headers()
            except ValueError as e:
                print(f"❌ {e} 카카오 캘린더 테스트를 건너뜁니다.")
                return

        # 1. 다가오는 일정 조회 (현재 구현된 메서드)
        print("--- 다가오는 일정 조회 ---")
        upcoming_events = await asyncio.to_thread(
            service.get_upcoming_events, calendar_id="primary", max_results=5
        )
        print_result(upcoming_events)

        # 2. 새 일정 생성 (현재 구현된 메서드)
        print("\n--- 새 이벤트 생성 ---")
        start_time = datetime.now() + timedelta(days=1)
        end_time = start_time + timedelta(hours=1)
        event_id = await asyncio.to_thread(
            service.create_event,
            title="API 테스트 이벤트",
            start_time=start_time,
            end_time=end_time,
            description="테스트 스크립트로 생성됨"
        )

        if event_id:
            print(f"✅ 새 이벤트 생성 성공! ID: {event_id}")
            print_result({"event_id": event_id})
        else:
            print("❌ 새 이벤트 생성 실패")

    except Exception as e:
        print(f"❌ 오류 발생: {e}")


async def main():
    """모든 API 테스트를 실행합니다."""
    await test_kakao_map_api()
    await test_duckduckgo_search_api()
    await test_kakao_calendar_api()
    print("\n✅ 모든 테스트가 완료되었습니다.")


if __name__ == "__main__":
    asyncio.run(main())
