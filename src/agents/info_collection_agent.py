"""
Info Collection Agent for gathering essential travel information.
"""
import re
from datetime import datetime
from typing import Any, Dict, List

from langchain.agents import AgentExecutor, create_openai_tools_agent
from langchain.tools import StructuredTool
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field

from ..config.settings import settings


class TravelInfoInput(BaseModel):
    """Input schema for travel info collection."""
    when: str = Field(description="여행 날짜 (예: 12월 25일, 2024년 1월 15일)")
    where: str = Field(description="여행 목적지")
    duration: str = Field(description="여행 기간 (예: 1박2일, 2박3일)")
    concept: str = Field(description="여행 컨셉 (예: 호캉스, 액티비티, 바다투어, 먹방투어)")


class InfoCollectionAgent:
    """Agent responsible for collecting essential travel information."""

    def __init__(self):
        self.llm = ChatOpenAI(
            model=settings.openai_model,
            streaming=True,
            temperature=0.3
        )
        self.tools = self._create_tools()
        self.prompt = ChatPromptTemplate.from_messages([
            ("system",
             "당신은 여행 계획을 위한 정보 수집 전문가입니다. "
             "사용자의 여행 계획 요청에서 다음 필수 정보를 수집해야 합니다:\n\n"
             "1. **언제**: 여행 날짜 (몇월 몇일)\n"
             "2. **어디**: 여행 목적지\n"
             "3. **며칠**: 여행 기간 (1박2일, 2박3일 등)\n"
             "4. **여행컨셉**: 어떤 활동을 하고 싶은지 (호캉스, 액티비티, 바다투어, 먹방투어 등)\n\n"
             "**중요한 규칙:**\n"
             "- 대화 기록을 주의 깊게 분석하여 이미 제공된 정보를 파악하세요.\n"
             "- 사용자가 단계적으로 정보를 제공할 수 있으므로, 이전 메시지에서 언급된 정보를 기억하고 활용하세요.\n"
             "- 누락된 정보만 추가로 질문하세요.\n"
             "- 모든 정보(언제, 어디, 며칠, 여행컨셉)가 수집되면 'collect_travel_info' 도구를 사용하여 정보를 정리하세요.\n"
             "- collect_travel_info 도구를 실행한 경우, 도구의 결과를 그대로 최종 응답으로 사용하세요. 추가 설명이나 수정은 하지 마세요.\n\n"
             "**정보 수집 예시:**\n"
             "- 사용자: '12월 25일에 여행 가려고 해' → '어느 지역으로 가시나요?', '몇 박 며칠 계획이신가요?', '어떤 컨셉의 여행을 원하시나요?' 질문\n"
             "- 사용자: '서울로 가려고 해' → '언제 가시나요?', '몇 박 며칠 계획이신가요?', '어떤 컨셉의 여행을 원하시나요?' 질문\n"
             "- 사용자: '2박3일로 계획 중이야' → '언제 가시나요?', '어디로 가시나요?', '어떤 컨셉의 여행을 원하시나요?' 질문\n"
             "- 사용자: '호캉스로 힐링하고 싶어' → '언제 가시나요?', '어디로 가시나요?', '몇 박 며칠 계획이신가요?' 질문\n\n"
             "**질문 예시:**\n"
             "- '언제 여행을 계획하고 계신가요? (예: 12월 25일)'\n"
             "- '어느 지역으로 여행을 가고 싶으신가요? (예: 서울, 부산, 제주도)'\n"
             "- '몇 박 며칠 여행을 계획하고 계신가요? (예: 1박2일, 2박3일)'\n"
             "- '어떤 컨셉의 여행을 원하시나요? (예: 호캉스, 액티비티, 바다투어, 먹방투어, 문화탐방, 쇼핑)'"),
            MessagesPlaceholder(variable_name="messages"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ])

        self.agent = create_openai_tools_agent(
            self.llm, self.tools, self.prompt)
        self.agent_executor = AgentExecutor(
            agent=self.agent,
            tools=self.tools,
            verbose=True,
            handle_parsing_errors=True
        )

    def _create_tools(self):
        """Create tools for the info collection agent."""

        def collect_travel_info(when: str, where: str, duration: str, concept: str) -> str:
            """여행 필수 정보를 수집하고 정리합니다."""

            # 날짜 형식 검증
            date_patterns = [
                r'\d{1,2}월\s*\d{1,2}일',  # 12월 25일
                r'\d{4}년\s*\d{1,2}월\s*\d{1,2}일',  # 2024년 12월 25일
                r'\d{1,2}/\d{1,2}',  # 12/25
                r'\d{4}/\d{1,2}/\d{1,2}'  # 2024/12/25
            ]

            is_valid_date = any(re.search(pattern, when)
                                for pattern in date_patterns)
            if not is_valid_date:
                return f"날짜 형식을 확인해주세요. '몇월 몇일' 형태로 입력해주세요. (예: 12월 25일)"

            # 기간 검증
            duration_patterns = [
                r'\d+박\s*\d+일',  # 1박2일, 2박3일
                r'당일치기',
                r'일일여행'
            ]

            is_valid_duration = any(re.search(pattern, duration)
                                    for pattern in duration_patterns)
            if not is_valid_duration:
                return f"여행 기간을 확인해주세요. '몇박몇일' 형태로 입력해주세요. (예: 1박2일, 2박3일, 당일치기)"

            return f"""
✅ **여행 정보가 수집되었습니다!**

📅 **여행 날짜**: {when}
📍 **여행 목적지**: {where}
⏰ **여행 기간**: {duration}
🎯 **여행 컨셉**: {concept}

이제 {where}에서 {concept} 컨셉으로 즐길 수 있는 관광지, 맛집, 숙소 정보를 검색하여 {duration} 여행 계획을 세워드리겠습니다!
"""

        collect_info_tool = StructuredTool.from_function(
            func=collect_travel_info,
            name="collect_travel_info",
            description="여행 필수 정보(언제, 어디, 며칠, 여행컨셉)를 수집하고 검증합니다.",
            args_schema=TravelInfoInput,
        )

        return [collect_info_tool]

    async def run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process info collection request."""
        try:
            messages = input_data.get("messages", [])

            response = await self.agent_executor.ainvoke({
                "messages": messages
            })

            return {
                "success": True,
                "data": response.get("output"),
                "message": "Info collection completed successfully."
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": "An error occurred during info collection."
            }

    def get_tools(self):
        """Returns the tools used by the agent."""
        return self.tools

    def extract_travel_info_from_text(self, text: str) -> Dict[str, str]:
        """텍스트에서 여행 정보를 추출합니다."""
        # 날짜 추출
        date_match = re.search(
            r'(\d{1,2}월\s*\d{1,2}일|\d{4}년\s*\d{1,2}월\s*\d{1,2}일)', text)
        when = date_match.group(1) if date_match else ""

        # 기간 추출
        duration_match = re.search(r'(\d+박\s*\d+일|당일치기|일일여행)', text)
        duration = duration_match.group(1) if duration_match else ""

        # 여행 컨셉 추출
        concept_keywords = [
            '호캉스', '액티비티', '바다투어', '먹방투어', '문화탐방', '쇼핑',
            '힐링', '체험', '관광', '맛집', '카페', '사진', '인스타',
            '등산', '트레킹', '해변', '온천', '스파', '골프'
        ]

        concept = ""
        for keyword in concept_keywords:
            if keyword in text:
                concept = keyword
                break

        return {
            "when": when,
            "where": "",  # 지역은 사용자가 직접 입력하도록 함
            "duration": duration,
            "concept": concept
        }
