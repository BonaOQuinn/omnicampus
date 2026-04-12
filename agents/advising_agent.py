"""
Advising Agent — academic policies, graduation, registration, GE, major changes.
"""
from agents.base_agent import BaseAgent


class AdvisingAgent(BaseAgent):
    name = "Advising"
    kb_id_env = "KB_ADVISING_ID"
    system_prompt = (
        "You are a CSU Academic Advising assistant. "
        "Answer questions about major changes, graduation requirements, "
        "add/drop deadlines, registration, general education, and academic policies. "
        "Be professional, precise, and cite specific policy names or catalog sections "
        "when available. If a question falls outside academic advising, "
        "direct the student to the appropriate campus office."
    )
    hitl_keywords = [
        "financial aid", "fafsa", "grant", "scholarship",
        "mental health", "counseling", "crisis", "suicide",
        "self-harm", "emergency", "overwhelmed", "depressed",
    ]
