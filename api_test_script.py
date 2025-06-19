import asyncio
import json
from datetime import datetime, timedelta

from dotenv import load_dotenv

from src.services.duckduckgo_service import DuckDuckGoService
from src.services.google_search_service import GoogleSearchService
from src.services.kakao_calendar_service import KakaoCalendarService
from src.services.kakao_service import KakaoMapService

# .env 파일을 로드하고, 기존 환경 변수를 덮어쓰도록 설정
load_dotenv(override=True)

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


async def test_google_search_api():
    """Google Search API를 테스트합니다."""
    print_header("웹 검색 (Google) API 테스트")
    try:
        service = GoogleSearchService()
        results = await service.search_web("파리 여행 정보", num_results=3)
        print_result(results)
    except ValueError as e:
        print(f"❌ {e} Google 검색 테스트를 건너뜁니다.")
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
    """카카오톡 캘린더 API의 생성, 조회, 수정, 삭제 기능을 테스트합니다."""
    print_header("카카오톡 캘린더 API CRUD 테스트")
    try:
        service = KakaoCalendarService()
        if not service.access_token:
            try:
                service._get_headers()
            except ValueError as e:
                print(f"❌ {e} 카카오 캘린더 테스트를 건너뜁니다.")
                return

        # --- 1. 테스트 전 일정 조회 ---
        print("--- 1. 테스트 전 일정 조회 ---")
        upcoming_events = await asyncio.to_thread(
            service.get_upcoming_events, calendar_id="primary", max_results=5
        )
        print("현재 등록된 일정:")
        print_result(upcoming_events)

        # --- 2. 새 이벤트 생성 ---
        print("\n--- 2. 새 이벤트 생성 ---")
        now = datetime.now()
        start_time = (now - timedelta(minutes=now.minute % 5,
                                      seconds=now.second,
                                      microseconds=now.microsecond)
                      + timedelta(days=1))
        end_time = start_time + timedelta(hours=1)
        event_id = await asyncio.to_thread(
            service.create_event,
            title="API 테스트 이벤트222222222",
            start_time=start_time,
            end_time=end_time,
            description="테스트 스크립트로 생성됨",
            reminders=[15],
            color="BLUE"
        )

        if not event_id:
            print("❌ 새 이벤트 생성 실패. 테스트를 중단합니다.")
            return

        print(f"✅ 새 이벤트 생성 성공! ID: {event_id}")
        print_result({"event_id": event_id})

        # --- 3. 생성된 이벤트 수정 ---
        print("\n--- 3. 생성된 이벤트 수정 ---")
        new_title = f"수정된 테스트 이벤트 ({now.strftime('%H:%M')})"
        update_success = await asyncio.to_thread(
            service.update_event,
            event_id=event_id,
            calendar_id="primary",
            title=new_title,
            color="RED"
        )
        if update_success:
            print(f"✅ 이벤트 수정 성공! (새 제목: {new_title}, 색상: RED)")
        else:
            print("❌ 이벤트 수정 실패.")

        # --- 4. 수정된 이벤트 삭제 ---
        print("\n--- 4. 수정된 이벤트 삭제 ---")
        delete_success = await asyncio.to_thread(
            service.delete_event,
            event_id=event_id
        )
        if delete_success:
            print(f"✅ 이벤트 삭제 성공! (ID: {event_id})")
        else:
            print(f"❌ 이벤트 삭제 실패. (ID: {event_id})")

        # --- 5. 테스트 후 최종 일정 조회 ---
        print("\n--- 5. 테스트 후 최종 일정 조회 ---")
        final_events = await asyncio.to_thread(
            service.get_upcoming_events, calendar_id="primary", max_results=5
        )
        print("최종 등록된 일정:")
        print_result(final_events)

    except Exception as e:
        print(f"❌ 오류 발생: {e}")


async def main():
    """모든 API 테스트를 실행합니다."""
    await test_kakao_map_api()
    await test_google_search_api()
    await test_duckduckgo_search_api()
    await test_kakao_calendar_api()
    print("\n✅ 모든 테스트가 완료되었습니다.")


if __name__ == "__main__":
    asyncio.run(main())
