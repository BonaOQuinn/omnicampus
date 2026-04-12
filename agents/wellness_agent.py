"""
Wellness Agent — counseling, mental health, crisis hotlines, TimelyCare, mindfulness.
ALWAYS escalates crisis/self-harm keywords to a human supervisor.
"""
from agents.base_agent import BaseAgent


class WellnessAgent(BaseAgent):
    name = "Wellness"
    kb_id_env = "KB_WELLNESS_ID"
    system_prompt = (
        "You are a CSU Student Wellness assistant. "
        "Help students find counseling services, mental health resources, "
        "crisis hotlines, TimelyCare, and mindfulness programs. "
        "Be warm, non-clinical, and immediately actionable. "
        "Always include the 24/7 crisis line (988 Suicide & Crisis Lifeline) "
        "when any distress is mentioned. "
        "If a student expresses immediate danger to themselves or others, "
        "instruct them to call 911 or go to the nearest emergency room immediately."
    )
    # Wellness agent ALWAYS escalates crisis language
    hitl_keywords = [
        "crisis", "suicide", "suicidal", "self-harm", "self harm",
        "hurt myself", "end my life", "overdose", "hopeless",
        "emergency", "can't go on", "cannot go on", "give up",
        "overwhelmed", "depressed", "anxious", "panic",
    ]
