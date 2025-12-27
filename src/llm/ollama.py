import json
from langchain_community.llms import Ollama
from typing import Dict


class LangChainSpeechEvaluator:
    def __init__(self, model="llama3"):
        self.llm = Ollama(model=model, temperature=0.3)

    def evaluate_speech(
        self,
        speaker: str,
        content: str,
        self_name: str,
        suspicion: Dict[str, float],
    ) -> Dict[str, str]:
        prompt = f"""
You are a player in a one-night werewolf game.

You are {self_name}.
Current suspicion levels: {suspicion}

You heard the following speech:
Speaker: {speaker}
Content: "{content}"

Answer ONLY in JSON:
{{"suspicion_delta": "increase" | "decrease" | "none"}}
"""

        response = self.llm.invoke(prompt)

        try:
            return json.loads(response)
        except Exception:
            return {"suspicion_delta": "none"}
