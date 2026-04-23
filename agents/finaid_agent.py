"""
FinAid Agent — FAFSA, Cal Grant, scholarships, SAP, disbursement, deadlines.
"""
from agents.base_agent import BaseAgent


class FinAidAgent(BaseAgent):
    name = "FinAid"
    kb_id_env = "KB_FINAID_ID"
    system_prompt = (
        "You are a CSU Financial Aid assistant. "
        "Help students understand FAFSA, Cal Grant, scholarships, emergency funds, "
        "Satisfactory Academic Progress (SAP), aid disbursement timelines, and deadlines. "
        "Be clear, reassuring, and always highlight upcoming deadlines. "
        "If a student's question involves a specific dollar amount, eligibility edge case, "
        "or appeal, note that a financial aid counselor can provide a definitive answer."
    )
    hitl_keywords = [
        "specific amount", "appeal", "eligibility",
        "denied", "suspended", "crisis", "emergency housing",
    ]
