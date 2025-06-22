# guardrails.py에 추가할 새로운 필터
from langchain_openai import ChatOpenAI
from openai import ContentFilterFinishReasonError


class LLMBasedFilter(ContentFilterFinishReasonError):
    def __init__(self):
        super().__init__("llm_semantic_filter")
        # 가드레일 전용으로 빠르고 저렴한 모델 사용
        self.guardrail_llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
        self.prompt = ChatPromptTemplate.from_template(
            """당신은 AI 어시스턴트의 안전성을 검토하는 가드레일입니다.
            주어진 내용이 다음 안전 정책 중 하나라도 위반하는지 판단하세요:
            1. 욕설 또는 공격적인 언어
            2. 위험하거나 불법적인 활동 조장
            3. 개인정보 포함
            4. 폭력적이거나 선정적인 내용

            판단 결과를 JSON 형식으로만 답변해주세요. (is_safe: boolean, reason: string)

            내용: {content}
            """
        )

    def check(self, content: str) -> Tuple[bool, Optional[str]]:
        chain = self.prompt | self.guardrail_llm | JsonOutputParser()
        result = chain.invoke({"content": content})
        if not result["is_safe"]:
            return False, result["reason"]
        return True, None
