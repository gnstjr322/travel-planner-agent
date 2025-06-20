"""
Share Agent for sharing travel plans.
"""
import json
import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import aiohttp

from ..prompts.base_prompts import prompt_manager
from ..prompts.guardrails import guardrail_system
from .base_agent import AgentResponse, BaseAgent


class ShareAgent(BaseAgent):
    """Agent responsible for sharing travel plans."""

    def __init__(self):
        super().__init__(
            name="ShareAgent",
            description="Handles sharing of travel plans through various formats and channels"
        )
        self.shared_plans: Dict[str, Dict] = {}  # In-memory storage for demo

    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process sharing request."""
        try:
            operation = input_data.get("operation", "")

            if operation == "create_share":
                return await self.create_shareable_link(input_data)
            elif operation == "export_pdf":
                return await self.export_to_pdf(input_data)
            elif operation == "export_json":
                return await self.export_to_json(input_data)
            elif operation == "get_shared":
                return await self.get_shared_plan(input_data)
            else:
                raise ValueError(f"Unknown operation: {operation}")

        except Exception as e:
            return AgentResponse(
                success=False,
                error=str(e),
                message="공유 작업 중 오류가 발생했습니다.",
                agent_name=self.name
            ).dict()

    async def create_shareable_link(self, plan_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a shareable link for the travel plan."""
        try:
            plan_id = str(uuid.uuid4())
            share_data = {
                "plan_id": plan_id,
                "plan_data": plan_data.get("plan_data", {}),
                "created_at": datetime.now().isoformat(),
                "expires_at": (datetime.now() + timedelta(days=30)).isoformat(),
                "access_count": 0
            }

            # Store in memory (in production, use proper database)
            self.shared_plans[plan_id] = share_data

            share_url = f"https://travel-planner.example.com/shared/{plan_id}"

            return AgentResponse(
                success=True,
                data={
                    "share_url": share_url,
                    "plan_id": plan_id,
                    "expires_at": share_data["expires_at"]
                },
                message="공유 링크가 생성되었습니다.",
                agent_name=self.name
            ).dict()

        except Exception as e:
            return AgentResponse(
                success=False,
                error=str(e),
                message="공유 링크 생성 중 오류가 발생했습니다.",
                agent_name=self.name
            ).dict()

    async def export_to_pdf(self, plan_data: Dict[str, Any]) -> Dict[str, Any]:
        """Export travel plan to PDF format."""
        try:
            # TODO: Implement PDF generation using reportlab or similar
            pdf_filename = f"travel_plan_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"

            return AgentResponse(
                success=True,
                data={
                    "pdf_filename": pdf_filename,
                    "download_url": f"/downloads/{pdf_filename}"
                },
                message="PDF 파일이 생성되었습니다.",
                agent_name=self.name
            ).dict()

        except Exception as e:
            return AgentResponse(
                success=False,
                error=str(e),
                message="PDF 생성 중 오류가 발생했습니다.",
                agent_name=self.name
            ).dict()

    async def export_to_json(self, plan_data: Dict[str, Any]) -> Dict[str, Any]:
        """Export travel plan to JSON format."""
        try:
            json_data = json.dumps(plan_data, ensure_ascii=False, indent=2)
            filename = f"travel_plan_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

            return AgentResponse(
                success=True,
                data={
                    "json_data": json_data,
                    "filename": filename
                },
                message="JSON 파일이 생성되었습니다.",
                agent_name=self.name
            ).dict()

        except Exception as e:
            return AgentResponse(
                success=False,
                error=str(e),
                message="JSON 생성 중 오류가 발생했습니다.",
                agent_name=self.name
            ).dict()

    async def get_shared_plan(self, query_data: Dict[str, Any]) -> Dict[str, Any]:
        """Retrieve a shared travel plan."""
        try:
            plan_id = query_data.get("plan_id", "")

            if plan_id not in self.shared_plans:
                raise ValueError("공유된 계획을 찾을 수 없습니다.")

            shared_plan = self.shared_plans[plan_id]

            # Check if expired
            expires_at = datetime.fromisoformat(shared_plan["expires_at"])
            if datetime.now() > expires_at:
                raise ValueError("공유 링크가 만료되었습니다.")

            # Increment access count
            shared_plan["access_count"] += 1

            return AgentResponse(
                success=True,
                data=shared_plan["plan_data"],
                message="공유된 계획을 조회했습니다.",
                agent_name=self.name
            ).dict()

        except Exception as e:
            return AgentResponse(
                success=False,
                error=str(e),
                message="공유된 계획 조회 중 오류가 발생했습니다.",
                agent_name=self.name
            ).dict()

    def get_tools(self) -> List[Any]:
        """Return sharing tools."""
        return []
