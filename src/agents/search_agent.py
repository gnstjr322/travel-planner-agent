"""
Search Agent for finding travel destinations and places.
"""
from typing import Any, Dict

from langchain import hub
from langchain.agents import AgentExecutor, create_react_agent
from langchain_core.prompts import PromptTemplate
from langchain_openai import ChatOpenAI

from ..config.settings import settings
from ..tools.search_tools import search_tools


class SearchAgent:
    """Agent responsible for searching travel destinations and places."""

    def __init__(self):
        self.llm = ChatOpenAI(
            model=settings.openai_model,
            streaming=True,
            temperature=settings.openai_temperature
        )
        self.tools = search_tools

        template = """주어진 최종 사용자의 질문에 답하기 위해 생각하고 행동하세요. 당신은 다음 도구에 접근할 수 있습니다:

{tools}

다음 형식을 사용하세요:

Question: 당신이 답해야 하는 사용자 질문
Thought: 당신은 항상 무엇을 해야 할지 생각해야 합니다.
Action: 수행할 행동, {tool_names} 중 하나여야 합니다.
Action Input: 행동에 대한 입력
Observation: 행동의 결과
Final Answer: 원래 질문에 대한 최종 답변

Question: {input}
Thought:{agent_scratchpad}"""

        self.prompt = PromptTemplate.from_template(template)
        self.agent = create_react_agent(self.llm, self.tools, self.prompt)
        self.agent_executor = AgentExecutor(
            agent=self.agent,
            tools=self.tools,
            verbose=True,
            handle_parsing_errors=True
        )

    async def run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process search request using the ReAct agent."""
        try:
            query = input_data.get("query", "")
            if not query:
                return {"success": False, "message": "Query is missing."}

            response = await self.agent_executor.ainvoke({
                "input": query,
                "chat_history": input_data.get("chat_history", [])
            })

            return {
                "success": True,
                "data": response.get("output"),
                "message": "Search completed successfully."
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": "An error occurred during search."
            }

    def get_tools(self):
        """Returns the tools used by the agent."""
        return self.tools
