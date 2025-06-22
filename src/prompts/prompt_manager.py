from pathlib import Path

import yaml
from langchain_core.prompts import (ChatPromptTemplate,
                                    HumanMessagePromptTemplate,
                                    SystemMessagePromptTemplate)


def load_prompt_template(agent_name: str, version: str = "v1") -> ChatPromptTemplate:
    """에이전트와 버전에 맞는 프롬프트 템플릿을 로드합니다."""
    prompt_path = Path(f"src/prompts/templates/{version}/{agent_name}.yml")

    if not prompt_path.exists():
        raise FileNotFoundError(f"Prompt file not found: {prompt_path}")

    with open(prompt_path, 'r', encoding='utf-8') as f:
        prompt_config = yaml.safe_load(f)

    # ChatPromptTemplate 형식에 맞게 생성
    # 예시: 시스템 프롬프트만 있는 경우
    return ChatPromptTemplate.from_messages([
        ("system", prompt_config['template']),
        ("human", "{messages}")
    ])
