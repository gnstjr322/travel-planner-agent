"""
Base prompt template system for multi-agent travel planner.
"""
import json
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict, List, Optional

import yaml


class PromptTemplate(ABC):
    """Base class for all prompt templates."""

    def __init__(self, name: str, version: str = "1.0"):
        self.name = name
        self.version = version
        self.created_at = datetime.now()
        self.metadata = {}

    @abstractmethod
    def render(self, **kwargs) -> str:
        """Render the prompt template with given parameters."""
        pass

    @abstractmethod
    def get_required_params(self) -> List[str]:
        """Return list of required parameters for this template."""
        pass

    def validate_params(self, params: Dict[str, Any]) -> bool:
        """Validate that all required parameters are provided."""
        required = set(self.get_required_params())
        provided = set(params.keys())
        missing = required - provided

        if missing:
            raise ValueError(f"Missing required parameters: {missing}")
        return True


class SystemPromptTemplate(PromptTemplate):
    """Template for system-level prompts."""

    def __init__(self, template: str, name: str, version: str = "1.0"):
        super().__init__(name, version)
        self.template = template

    def render(self, **kwargs) -> str:
        """Render the system prompt."""
        self.validate_params(kwargs)
        return self.template.format(**kwargs)

    def get_required_params(self) -> List[str]:
        """Extract required parameters from template."""
        import re

        # Find all {param} patterns in template
        params = re.findall(r'\{(\w+)\}', self.template)
        return list(set(params))


class UserPromptTemplate(PromptTemplate):
    """Template for user prompts."""

    def __init__(self, template: str, name: str, version: str = "1.0"):
        super().__init__(name, version)
        self.template = template

    def render(self, **kwargs) -> str:
        """Render the user prompt."""
        self.validate_params(kwargs)
        return self.template.format(**kwargs)

    def get_required_params(self) -> List[str]:
        """Extract required parameters from template."""
        import re
        params = re.findall(r'\{(\w+)\}', self.template)
        return list(set(params))


class PromptManager:
    """Central manager for all prompt templates."""

    def __init__(self):
        self.templates: Dict[str, PromptTemplate] = {}
        self.load_default_templates()

    def register_template(self, template: PromptTemplate):
        """Register a new prompt template."""
        self.templates[template.name] = template

    def get_template(self, name: str) -> PromptTemplate:
        """Get a prompt template by name."""
        if name not in self.templates:
            raise ValueError(f"Template '{name}' not found")
        return self.templates[name]

    def render_prompt(self, template_name: str, **kwargs) -> str:
        """Render a specific prompt template."""
        template = self.get_template(template_name)
        return template.render(**kwargs)

    def list_templates(self) -> List[str]:
        """List all available template names."""
        return list(self.templates.keys())

    def load_default_templates(self):
        """Load default prompt templates."""
        # Search Agent Templates
        search_system = SystemPromptTemplate(
            name="search_system",
            template="""당신은 전문 여행지 검색 에이전트입니다.
사용자의 요청에 따라 정확하고 유용한 여행지 정보를 제공해주세요.

다음 규칙을 반드시 준수하세요:
1. 실제로 존재하는 장소만 추천하세요
2. 정확한 주소와 운영시간을 제공하세요
3. 가격 정보가 있다면 최신 정보를 기준으로 하세요
4. 계절별 특징이나 방문 시 주의사항을 포함하세요
5. 대중교통 접근 방법을 알려주세요

응답 형식:
- 장소명: 
- 주소: 
- 설명: 
- 추천 이유: 
- 방문 최적 시간: 
- 예상 소요시간: 
- 주변 관광지: 
- 교통 정보: """
        )

        search_user = UserPromptTemplate(
            name="search_user",
            template="""다음 조건으로 여행지를 검색해주세요:

검색어: {query}
지역: {location}
카테고리: {category}
추가 조건: {additional_conditions}

위 조건에 맞는 여행지를 3-5곳 추천해주세요."""
        )

        # Planner Agent Templates
        planner_system = SystemPromptTemplate(
            name="planner_system",
            template="""당신은 전문 여행 계획 수립 에이전트입니다.
사용자의 요구사항을 바탕으로 실용적이고 실현 가능한 여행 일정을 작성해주세요.

계획 수립 원칙:
1. 예산 내에서 최대 만족도를 제공하세요
2. 이동 시간과 교통비를 고려하세요
3. 식사, 휴식 시간을 적절히 배분하세요
4. 날씨와 계절 특성을 반영하세요
5. 비상 계획과 예비 옵션을 포함하세요

응답 형식:
## 여행 개요
- 목적지: 
- 기간: 
- 예산: 
- 인원: 

## 일차별 일정
### 1일차
- 시간: 활동 (예산)

## 예상 총 비용
- 교통비: 
- 숙박비: 
- 식비: 
- 관광비: 
- 기타: 

## 준비물 체크리스트

## 유용한 팁"""
        )

        planner_user = UserPromptTemplate(
            name="planner_user",
            template="""다음 '사용자 원본 요청'과 '참고 검색 결과'를 바탕으로 상세하고 실행 가능한 여행 계획을 세워주세요.

### 사용자 원본 요청
{query}

### 참고할 검색 결과
{search_results}

'여행 개요', '일차별 일정', '예상 총 비용', '준비물 체크리스트' 등을 포함하여, 'planner_system' 프롬프트에 정의된 전체 응답 형식에 맞춰서 계획을 작성해주세요."""
        )

        # Calendar Agent Templates
        calendar_system = SystemPromptTemplate(
            name="calendar_system",
            template="""당신은 여행 일정 캘린더 관리 에이전트입니다.
여행 계획을 캘린더 이벤트로 변환하고 관리하는 업무를 담당합니다.

작업 원칙:
1. 일정을 명확하고 구체적인 이벤트로 분할하세요
2. 적절한 알림 시간을 설정하세요
3. 위치 정보를 정확히 입력하세요
4. 예약 확인 번호나 중요 정보를 메모에 포함하세요
5. 이동 시간을 고려한 버퍼 시간을 두세요

이벤트 형식:
- 제목: [활동명] 
- 시작시간: YYYY-MM-DD HH:MM
- 종료시간: YYYY-MM-DD HH:MM
- 위치: 주소
- 설명: 상세 정보
- 알림: 시간"""
        )

        calendar_user = UserPromptTemplate(
            name="calendar_user",
            template="""당신은 사용자의 요청과 주어진 여행 계획을 분석하여 캘린더 이벤트 생성을 위한 정확한 정보를 추출하는 전문가입니다.

다음 정보를 바탕으로 JSON 형식의 이벤트 데이터를 생성해주세요.

### 현재 시간
{current_time}

### 사용자 요청
"{query}"

### 여행 계획
{travel_plan}

### 추출해야 할 정보
- `title`: 이벤트의 제목 (예: "제주도 3박 4일 여행")
- `start_time`: 이벤트 시작 시간 (ISO 8601 형식: YYYY-MM-DDTHH:MM:SS)
- `end_time`: 이벤트 종료 시간 (ISO 8601 형식: YYYY-MM-DDTHH:MM:SS)
- `location`: 이벤트 장소 이름 (문자열, 예: "제주 국제공항")
- `description`: 이벤트에 대한 상세 설명 (여행 계획 요약, 주요 활동 등)
- `reminders`: 이벤트 시작 전 알림을 받을 시간(분 단위)의 숫자 배열 (예: [15, 30] -> 15분, 30분 전 알림). 없으면 빈 배열 `[]`.

만약 사용자 요청이나 여행 계획에서 특정 시간 정보(예: 오후 3시)를 찾을 수 없다면, 하루 종일 진행되는 일정으로 간주하고 시간 부분은 09:00:00으로 설정해주세요. 날짜 정보가 없다면 현재 시간 기준으로 내일부터의 날짜로 가정해주세요.

JSON 데이터만 반환해주세요. 다른 설명은 필요 없습니다.
"""
        )

        # Share Agent Templates
        share_system = SystemPromptTemplate(
            name="share_system",
            template="""당신은 여행 계획 공유 전문 에이전트입니다.
여행 계획을 다양한 형태로 포맷팅하고 공유 가능한 형태로 변환합니다.

공유 형식별 특징:
1. 웹 링크: 간단한 URL로 접근 가능
2. PDF: 인쇄 가능한 고품질 문서
3. 이미지: SNS 공유용 시각적 자료
4. JSON: 다른 앱과의 데이터 연동

포맷팅 원칙:
- 읽기 쉽고 시각적으로 매력적으로
- 핵심 정보를 우선 배치
- 연락처와 예약 정보 강조
- 브랜딩과 디자인 일관성 유지"""
        )

        # Router Agent Template
        router_system = SystemPromptTemplate(
            name="router_system",
            template="""당신은 사용자 요청의 의도를 파악하여 어떤 에이전트에게 작업을 라우팅해야 할지 결정하는 지능형 라우터입니다.

사용자의 최신 요청과 현재 대화 상태를 바탕으로 다음에 실행할 에이전트를 결정해주세요.

[현재 상태]
- 검색 결과가 있는가? {has_search_results}
- 수립된 계획이 있는가? {has_plan}
- 이전에 실행된 에이전트: {executed_agents}

[사용자 요청]
"{query}"

[라우팅 결정]
사용자 요청과 `이전에 실행된 에이전트` 목록을 분석하여 다음 중 가장 적절한 하나를 선택하여 응답하세요. **가장 중요한 규칙은 동일한 작업을 반복하지 않는 것입니다.**

- `search`: 여행 장소, 맛집, 활동 등 **새로운 정보 검색**이 필요할 때. **`이전에 실행된 에이전트`에 'search'가 있다면 절대 다시 'search'를 선택하지 마세요.**
- `planner`: 여행 계획 수립, 수정, 또는 최적화가 필요할 때.
- `calendar`: 수립된 계획을 캘린더에 등록하거나 수정해야 할 때.
- `share`: 여행 계획을 다른 사람과 공유하고 싶을 때.
- `conversation`: 사용자가 단순히 인사하거나, 일반적인 대화를 시도하거나, 여행과 무관한 질문을 할 때.
- `end`: **요청된 작업이 이미 완료되었을 때.** 예를 들어, 사용자가 '검색'을 요청했고 `이전에 실행된 에이전트` 목록에 이미 'search'가 있다면, 작업이 완료된 것이므로 'end'를 선택해야 합니다. 또는 사용자가 대화를 끝내고 싶을 때 (예: "고마워", "수고했어")도 해당됩니다.

오직 `search`, `planner`, `calendar`, `share`, `conversation`, `end` 중 하나만 소문자로 응답해야 합니다. 다른 설명은 절대 추가하지 마세요."""
        )

        # Register all templates
        self.register_template(search_system)
        self.register_template(search_user)
        self.register_template(planner_system)
        self.register_template(planner_user)
        self.register_template(calendar_system)
        self.register_template(calendar_user)
        self.register_template(share_system)
        self.register_template(router_system)


# Global prompt manager instance
prompt_manager = PromptManager()
