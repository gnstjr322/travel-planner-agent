"""
캘린더 에이전트 - KakaoTalk Calendar API 연동
"""

import json
import re
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from langchain_openai import ChatOpenAI

from ..config.settings import settings
from ..prompts.base_prompts import prompt_manager
from ..services.kakao_calendar_service import KakaoCalendarService
from ..utils.logger import logger
from .base_agent import AgentResponse, BaseAgent


class CalendarAgent(BaseAgent):
    """캘린더 관리 에이전트"""

    def __init__(self):
        super().__init__("calendar", "캘린더 일정 관리")
        self.calendar_service = KakaoCalendarService()
        self.llm = ChatOpenAI(
            model=settings.openai_model,
            temperature=0,
        )

    def get_tools(self) -> List[Any]:
        """CalendarAgent는 LangChain Tool을 직접 사용하지 않으므로 빈 리스트를 반환합니다."""
        return []

    async def process(
        self, query: str, context: Optional[Dict[str, Any]] = None
    ) -> AgentResponse:
        """LLM을 사용하여 캘린더 관련 요청 처리"""
        try:
            logger.info(f"캘린더 에이전트 처리 시작: {query}")

            if not self.calendar_service.is_available():
                return AgentResponse(
                    success=False,
                    message="⚠️ 카카오톡 캘린더 서비스에 연결할 수 없습니다. 설정을 확인해주세요.",
                    error="calendar_service_unavailable",
                    agent_name=self.name,
                )

            travel_plan_str = json.dumps(context.get(
                "travel_plan", {}), ensure_ascii=False) if context else "{}"

            # LLM을 사용하여 이벤트 정보 추출
            prompt = prompt_manager.render_prompt(
                "calendar_user",
                current_time=datetime.now().isoformat(),
                query=query,
                travel_plan=travel_plan_str,
            )

            response = await self.llm.ainvoke(prompt)
            event_data = self._parse_llm_response(str(response.content))

            if not event_data:
                return AgentResponse(
                    success=False,
                    message="캘린더에 등록할 정보를 추출하지 못했습니다.",
                    error="parsing_failed",
                    agent_name=self.name,
                )

            # TODO: Add logic for different operations (create, update, delete) based on LLM output
            # For now, we assume creation.

            return await self._create_schedule_from_data(event_data)

        except Exception as e:
            logger.error(f"캘린더 에이전트 처리 중 오류: {str(e)}")
            return AgentResponse(
                success=False,
                message=f"캘린더 처리 중 오류가 발생했습니다: {str(e)}",
                error=str(e),
                agent_name=self.name,
            )

    def _parse_llm_response(self, response_content: str) -> Optional[Dict[str, Any]]:
        """LLM의 응답(JSON)을 파싱합니다."""
        try:
            # LLM 응답에서 JSON 블록만 추출
            match = re.search(r"```json\n(.*?)\n```",
                              response_content, re.DOTALL)
            if match:
                json_str = match.group(1)
            else:
                json_str = response_content

            return json.loads(json_str)
        except (json.JSONDecodeError, TypeError) as e:
            logger.error(f"LLM 응답 파싱 실패: {e}\n응답 내용: {response_content}")
            return None

    async def _create_schedule_from_data(self, event_data: Dict[str, Any]) -> AgentResponse:
        """추출된 데이터를 기반으로 캘린더 이벤트를 생성합니다."""
        try:
            now = datetime.now()
            title = event_data.get("title", "새로운 여행 일정")

            start_str = event_data.get("start_time")
            end_str = event_data.get("end_time")

            start_dt = datetime.fromisoformat(
                start_str) if start_str else now + timedelta(days=1, hours=9)
            end_dt = datetime.fromisoformat(
                end_str) if end_str else start_dt + timedelta(days=1)

            location_name = event_data.get("location")
            location_dict = {"name": location_name} if location_name else None

            description = event_data.get("description")
            reminders = event_data.get("reminders")

            # Prepare event arguments
            event_args = {
                "title": title,
                "start_time": start_dt,
                "end_time": end_dt,
                "description": description or "",
            }
            if location_dict:
                event_args["location"] = location_dict
            if reminders:
                event_args["reminders"] = reminders

            event_id = self.calendar_service.create_event(**event_args)

            if event_id:
                start_str_formatted = start_dt.strftime("%Y년 %m월 %d일 %H:%M")
                end_str_formatted = end_dt.strftime("%Y년 %m월 %d일 %H:%M")
                content_msg = (
                    f"📅 **여행 일정이 카카오톡 캘린더에 등록되었습니다!**\n\n"
                    f"📌 **제목**: {title}\n"
                    f"⏰ **기간**: {start_str_formatted} ~ {end_str_formatted}\n"
                    f"📍 **장소**: {location_name or '미지정'}\n\n"
                    f"자세한 내용은 카카오톡 캘린더를 확인해주세요."
                )
                return AgentResponse(
                    success=True,
                    message=content_msg,
                    data={"event_id": event_id,
                          "calendar_action": "create_success"},
                    agent_name=self.name,
                )
            else:
                return AgentResponse(
                    success=False,
                    message="❌ 카카오톡 캘린더 일정 생성에 실패했습니다.",
                    error="create_failed_kakao",
                    agent_name=self.name,
                )
        except Exception as e:
            logger.error(f"일정 생성 중 오류: {e}")
            return AgentResponse(
                success=False,
                message=f"일정 생성 중 오류가 발생했습니다: {str(e)}",
                error=str(e),
                agent_name=self.name,
            )
