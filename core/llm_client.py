"""
core/llm_client.py

Thin wrapper around a locally running Ollama instance.
No cloud calls -- this only ever talks to http://localhost:11434, which
Ollama serves on your own machine. If Ollama isn't running, we fall back
to a clearly-labeled stub response so the rest of the pipeline is still
testable end-to-end without the LLM.

Setup on your machine (not needed in this sandbox):
    1. Install Ollama: https://ollama.com/download
    2. ollama pull phi3:mini      (or gemma:2b, whichever you prefer)
    3. ollama serve               (usually starts automatically)
"""

import json
import requests

OLLAMA_URL = "http://localhost:11434/api/generate"
DEFAULT_MODEL = "phi3:mini"


class LocalLLM:
    def __init__(self, model: str = DEFAULT_MODEL, timeout: int = 30):
        self.model = model
        self.timeout = timeout

    def is_available(self) -> bool:
        try:
            requests.get("http://localhost:11434", timeout=2)
            return True
        except requests.exceptions.RequestException:
            return False

    def generate(self, prompt: str) -> str:
        """
        Sends a prompt to the local Ollama model and returns the plain-text
        response. Falls back to a stub if Ollama isn't reachable, so you can
        develop/test the rest of the pipeline offline-from-Ollama too.
        """
        if not self.is_available():
            return self._stub_response(prompt)

        try:
            resp = requests.post(
                OLLAMA_URL,
                json={"model": self.model, "prompt": prompt, "stream": False},
                timeout=self.timeout,
            )
            resp.raise_for_status()
            return resp.json().get("response", "").strip()
        except requests.exceptions.RequestException as e:
            return f"[LLM ERROR - falling back to stub] {e}\n\n" + self._stub_response(prompt)

    def _stub_response(self, prompt: str) -> str:
        return (
            "[STUB RESPONSE -- Ollama not detected on localhost:11434]\n"
            "This is a placeholder so you can test the pipeline without the LLM running.\n"
            "Once Ollama is running locally with your model pulled, this will be replaced "
            "by a real explanation generated from the prompt below:\n\n"
            f"--- prompt sent ---\n{prompt}"
        )
