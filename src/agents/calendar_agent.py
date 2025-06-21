"""
캘린더 에이전트 - 여행 계획을 카카오 캘린더에 등록
"""

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

from src.tools.calendar_tools import (add_travel_plan_to_calendar,
                                      check_calendar_availability)
from src.utils.logger import get_logger

logger = get_logger(__name__)


class CalendarAgent:
    """여행 계획을 카카오 캘린더에 등록하는 전문 에이전트"""

    def __init__(self, llm: ChatOpenAI):
        self.llm = llm
        self.tools = [add_travel_plan_to_calendar, check_calendar_availability]

    async def process_travel_plan(self, travel_plan: str, destination: str = None, travel_date: str = None) -> str:
        """
        여행 계획을 분석하고 카카오 캘린더에 등록

        Args:
            travel_plan: 완성된 여행 계획 텍스트
            destination: 여행 목적지 (선택사항)
            travel_date: 여행 날짜 (선택사항)

        Returns:
            캘린더 등록 결과 메시지
        """
        try:
            logger.info("CalendarAgent: 여행 계획 캘린더 등록 시작")

            # 시스템 메시지
            system_msg = SystemMessage(content="""
당신은 여행 계획을 카카오 캘린더에 등록하는 전문가입니다.

**임무:**
1. 제공된 여행 계획을 분석하여 다음 정보를 추출합니다:
   - 여행 목적지
   - 여행 날짜/기간
   - 주요 활동 및 장소들
   - 시간별 일정 (있는 경우)

2. `add_travel_plan_to_calendar` 도구를 사용하여 캘린더에 등록합니다.

3. 등록 결과를 사용자에게 친근하게 보고합니다.

**중요 사항:**
- 날짜 정보가 명확하지 않은 경우, 사용자에게 구체적인 날짜를 요청하세요.
- 일정 충돌을 방지하기 위해 필요시 `check_calendar_availability` 도구를 사용하세요.
- 등록 성공 시 구체적인 일정 내용을 요약해서 알려주세요.
""")

            # 사용자 메시지 구성
            user_content = f"다음 여행 계획을 카카오 캘린더에 등록해주세요:\n\n{travel_plan}"
            if destination:
                user_content += f"\n\n목적지: {destination}"
            if travel_date:
                user_content += f"\n여행 날짜: {travel_date}"

            user_msg = HumanMessage(content=user_content)

            # LLM 호출하여 캘린더 등록 처리
            messages = [system_msg, user_msg]

            # 도구 바인딩
            llm_with_tools = self.llm.bind_tools(self.tools)
            response = await llm_with_tools.ainvoke(messages)

            # 도구 호출이 있는 경우 실행
            if response.tool_calls:
                messages.append(response)

                for tool_call in response.tool_calls:
                    tool_name = tool_call["name"]
                    tool_args = tool_call["args"]

                    logger.info(f"CalendarAgent: {tool_name} 도구 실행 중...")

                    if tool_name == "add_travel_plan_to_calendar":
                        result = await add_travel_plan_to_calendar.ainvoke(tool_args)
                    elif tool_name == "check_calendar_availability":
                        result = await check_calendar_availability.ainvoke(tool_args)
                    else:
                        result = f"알 수 없는 도구: {tool_name}"

                    # 도구 실행 결과를 메시지에 추가
                    from langchain_core.messages import ToolMessage
                    messages.append(ToolMessage(
                        content=str(result),
                        tool_call_id=tool_call["id"]
                    ))

                # 최종 응답 생성
                final_response = await self.llm.ainvoke(messages)
                result = final_response.content
            else:
                result = response.content

            logger.info("CalendarAgent: 캘린더 등록 처리 완료")
            return result

        except Exception as e:
            error_msg = f"캘린더 등록 중 오류가 발생했습니다: {str(e)}"
            logger.error(f"CalendarAgent 오류: {error_msg}")
            return error_msg

    def get_calendar_registration_guide(self) -> str:
        """캘린더 등록 안내 메시지 반환"""
        return """
📅 **캘린더 등록 안내**

여행 계획이 완성되었습니다! 카카오 캘린더에 등록하시겠습니까?

**등록 시 포함되는 정보:**
- 여행 제목 및 목적지
- 여행 날짜 및 기간
- 주요 방문 장소 및 활동
- 맛집 및 카페 정보

**필요한 정보:**
- 구체적인 여행 날짜 (예: 2024-03-15)
- 여행 기간 (당일치기/1박2일 등)

날짜를 알려주시면 바로 캘린더에 등록해드리겠습니다! 🎯
"""

