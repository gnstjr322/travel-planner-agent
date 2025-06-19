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
            template="""다음 조건으로 여행 계획을 세워주세요:

목적지: {destination}
여행 기간: {start_date} ~ {end_date}
예산: {budget}
인원수: {group_size}명
숙박 타입: {accommodation_type}
여행 스타일: {travel_style}
선호 사항: {preferences}
제외 사항: {exclusions}

상세하고 실행 가능한 일정을 작성해주세요."""
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

        # Register all templates
        self.register_template(search_system)
        self.register_template(search_user)
        self.register_template(planner_system)
        self.register_template(planner_user)
        self.register_template(calendar_system)
        self.register_template(share_system)


# Global prompt manager instance
prompt_manager = PromptManager()
