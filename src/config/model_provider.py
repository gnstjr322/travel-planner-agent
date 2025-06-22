'''
모델 제공사에 따라 다른 모델 객체를 생성하는 함수

src/config/models.yml 파일을 로드하여 모델 정보를 가져오고,
에이전트 이름에 맞는 모델 별칭을 찾아 해당 모델 정보를 반환

사용 예시: multi_agent_system.py
llm = get_llm_for_agent("planner_agent")

'''
import yaml
from langchain_openai import ChatOpenAI

# from langchain_google_genai import ChatGoogleGenerativeAI # 향후 확장


def load_model_config():
    """models.yml 파일을 로드합니다."""
    with open("src/config/models.yml", 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


def get_llm_for_agent(agent_name: str):
    """에이전트 이름에 맞는 LLM 객체를 반환합니다."""
    config = load_model_config()

    # 에이전트에 매핑된 모델 별칭 가져오기
    agent_mapping = config['agent_model_mapping']
    model_alias = agent_mapping.get(agent_name, agent_mapping['default'])

    # 별칭에 해당하는 모델 정보 찾기
    model_info = next(
        (m for m in config['models'] if m['alias'] == model_alias), None)

    if not model_info:
        raise ValueError(
            f"Model alias '{model_alias}' not found in models.yml")

    provider = model_info['provider']
    model_name = model_info['name']
    params = model_info.get('parameters', {})

    # 제공사에 따라 다른 모델 객체 생성
    if provider == "openai":
        return ChatOpenAI(model=model_name, **params)
    # elif provider == "google":
    #     return ChatGoogleGenerativeAI(model=model_name, **params)
    else:
        raise ValueError(f"Unsupported provider: {provider}")
