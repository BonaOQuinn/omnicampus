"""
BaseAgent — shared RAG query, Omnara logging, and HITL logic.
All domain agents inherit from this class.
"""
import uuid
from core.bedrock_client import query_knowledge_base
from core.omnara_client import log_event, send_status


class BaseAgent:
    name: str = "Base"
    kb_id_env: str = ""          # env var name holding the KB ID
    system_prompt: str = ""
    hitl_keywords: list[str] = []

    def __init__(self):
        import os
        self.kb_id: str = os.getenv(self.kb_id_env, "")
        self.instance_id: str = str(uuid.uuid4())[:8]

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def answer(self, question: str) -> dict:
        """
        Process a student question and return:
        {
          'agent': str,
          'instance_id': str,
          'answer': str,
          'sources': list[str],
          'hitl_triggered': bool,
          'supervisor_reply': str | None,
        }
        """
        log_event(self.name, f"Question received: {question}", self.instance_id)

        hitl_needed = self._needs_hitl(question)
        supervisor_reply = None

        if hitl_needed:
            log_event(self.name, "HITL triggered — notifying supervisor", self.instance_id)
            supervisor_reply = send_status(
                self.name,
                f"Sensitive question requires human review:\n\"{question}\"",
                self.instance_id,
                requires_input=True,
            )
            log_event(self.name, f"Supervisor replied: {supervisor_reply}", self.instance_id)

        log_event(self.name, "Querying Bedrock Knowledge Base", self.instance_id)
        result = query_knowledge_base(
            kb_id=self.kb_id,
            question=question,
            system_prompt=self.system_prompt,
        )
        log_event(self.name, "Answer generated", self.instance_id)

        return {
            "agent": self.name,
            "instance_id": self.instance_id,
            "answer": result["answer"],
            "sources": result["sources"],
            "hitl_triggered": hitl_needed,
            "supervisor_reply": supervisor_reply,
        }

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _needs_hitl(self, question: str) -> bool:
        q_lower = question.lower()
        return any(kw in q_lower for kw in self.hitl_keywords)
