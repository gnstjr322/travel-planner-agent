"""
LLM Guardrails system for content filtering and safety.
"""
import re
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple


class GuardrailViolation(Exception):
    """Exception raised when content violates guardrails."""

    def __init__(self, violation_type: str, message: str, content: str = ""):
        self.violation_type = violation_type
        self.message = message
        self.content = content
        self.timestamp = datetime.now()
        super().__init__(f"{violation_type}: {message}")


class ContentFilter:
    """Base class for content filtering."""

    def __init__(self, name: str):
        self.name = name

    def check(self, content: str) -> Tuple[bool, Optional[str]]:
        """Check if content passes the filter. Returns (is_safe, reason)."""
        raise NotImplementedError


class ProfanityFilter(ContentFilter):
    """Filter for inappropriate language."""

    def __init__(self):
        super().__init__("profanity")
        # 한국어 부적절한 언어 패턴
        self.blocked_patterns = [
            r'시발', r'씨발', r'개새끼', r'병신', r'좆', r'섹스',
            r'포르노', r'마약', r'도박', r'사기', r'불법'
        ]

    def check(self, content: str) -> Tuple[bool, Optional[str]]:
        """Check for profanity in content."""
        content_lower = content.lower()

        for pattern in self.blocked_patterns:
            if re.search(pattern, content_lower):
                return False, f"부적절한 언어 감지: {pattern}"

        return True, None


class TravelSafetyFilter(ContentFilter):
    """Filter for travel safety concerns."""

    def __init__(self):
        super().__init__("travel_safety")
        self.dangerous_patterns = [
            r'위험지역', r'테러', r'전쟁', r'분쟁지역', r'출입금지',
            r'극한스포츠', r'무허가', r'불법입국', r'밀입국'
        ]

    def check(self, content: str) -> Tuple[bool, Optional[str]]:
        """Check for travel safety issues."""
        content_lower = content.lower()

        for pattern in self.dangerous_patterns:
            if re.search(pattern, content_lower):
                return False, f"여행 안전 우려사항 감지: {pattern}"

        return True, None


class MisinformationFilter(ContentFilter):
    """Filter for potential misinformation."""

    def __init__(self):
        super().__init__("misinformation")
        self.suspicious_patterns = [
            r'100% 확실', r'절대 안전', r'무조건', r'보장합니다',
            r'비밀 장소', r'숨겨진', r'아무도 모르는'
        ]

    def check(self, content: str) -> Tuple[bool, Optional[str]]:
        """Check for potential misinformation."""
        content_lower = content.lower()

        for pattern in self.suspicious_patterns:
            if re.search(pattern, content_lower):
                return False, f"과장/허위정보 가능성: {pattern}"

        return True, None


class PrivacyFilter(ContentFilter):
    """Filter for privacy-sensitive information."""

    def __init__(self):
        super().__init__("privacy")
        self.sensitive_patterns = [
            r'\d{3}-\d{4}-\d{4}',  # 전화번호
            r'\d{6}-\d{7}',        # 주민번호
            r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}',  # 이메일
            r'비밀번호', r'패스워드', r'개인정보'
        ]

    def check(self, content: str) -> Tuple[bool, Optional[str]]:
        """Check for privacy-sensitive information."""
        for pattern in self.sensitive_patterns:
            if re.search(pattern, content):
                return False, f"개인정보 포함 가능성: 민감정보 패턴 감지"

        return True, None


class GuardrailSystem:
    """Main guardrail system that coordinates all filters."""

    def __init__(self):
        self.filters: List[ContentFilter] = [
            ProfanityFilter(),
            TravelSafetyFilter(),
            MisinformationFilter(),
            PrivacyFilter()
        ]
        self.violation_log: List[GuardrailViolation] = []
        self.enabled = True

    def add_filter(self, filter_instance: ContentFilter):
        """Add a custom filter to the system."""
        self.filters.append(filter_instance)

    def remove_filter(self, filter_name: str):
        """Remove a filter by name."""
        self.filters = [f for f in self.filters if f.name != filter_name]

    def check_content(self, content: str, agent_name: str = "") -> Dict[str, Any]:
        """
        Check content against all filters.
        Returns: {
            "is_safe": bool,
            "violations": List[Dict],
            "filtered_content": str,
            "warnings": List[str]
        }
        """
        if not self.enabled:
            return {
                "is_safe": True,
                "violations": [],
                "filtered_content": content,
                "warnings": []
            }

        violations = []
        warnings = []

        for filter_instance in self.filters:
            try:
                is_safe, reason = filter_instance.check(content)

                if not is_safe:
                    violation = {
                        "filter_name": filter_instance.name,
                        "reason": reason,
                        "agent_name": agent_name,
                        "timestamp": datetime.now().isoformat()
                    }
                    violations.append(violation)

                    # Log violation
                    self.violation_log.append(
                        GuardrailViolation(
                            violation_type=filter_instance.name,
                            message=reason,
                            content=content[:100]  # 처음 100자만 로깅
                        )
                    )

            except Exception as e:
                warnings.append(
                    f"Filter {filter_instance.name} error: {str(e)}")

        is_safe = len(violations) == 0

        # 안전하지 않은 경우 대체 텍스트 제공
        filtered_content = content
        if not is_safe:
            filtered_content = self._generate_safe_alternative(
                content, violations)

        return {
            "is_safe": is_safe,
            "violations": violations,
            "filtered_content": filtered_content,
            "warnings": warnings
        }

    def _generate_safe_alternative(self, original_content: str, violations: List[Dict]) -> str:
        """Generate a safe alternative when content violates guardrails."""
        violation_types = [v["filter_name"] for v in violations]

        if "profanity" in violation_types:
            return "죄송합니다. 부적절한 표현이 포함된 요청은 처리할 수 없습니다. 정중한 언어로 다시 요청해주세요."

        if "travel_safety" in violation_types:
            return "안전상의 이유로 해당 여행지나 활동은 추천드릴 수 없습니다. 안전한 대안을 찾아드릴까요?"

        if "misinformation" in violation_types:
            return "정확하지 않은 정보가 포함될 수 있어 재검토가 필요합니다. 보다 신뢰할 수 있는 정보로 다시 안내드리겠습니다."

        if "privacy" in violation_types:
            return "개인정보가 포함된 것 같습니다. 개인정보는 제외하고 다시 요청해주세요."

        return "요청하신 내용에 문제가 있어 처리할 수 없습니다. 다른 방식으로 요청해주세요."

    def get_violation_stats(self) -> Dict[str, Any]:
        """Get statistics about violations."""
        if not self.violation_log:
            return {"total_violations": 0, "by_type": {}}

        by_type = {}
        for violation in self.violation_log:
            violation_type = violation.violation_type
            by_type[violation_type] = by_type.get(violation_type, 0) + 1

        return {
            "total_violations": len(self.violation_log),
            "by_type": by_type,
            "recent_violations": [
                {
                    "type": v.violation_type,
                    "message": v.message,
                    "timestamp": v.timestamp.isoformat()
                }
                for v in self.violation_log[-5:]  # 최근 5개
            ]
        }

    def enable_guardrails(self):
        """Enable the guardrail system."""
        self.enabled = True

    def disable_guardrails(self):
        """Disable the guardrail system (for testing only)."""
        self.enabled = False


# Global guardrail system instance
guardrail_system = GuardrailSystem()
