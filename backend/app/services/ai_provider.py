from __future__ import annotations

from typing import Protocol

from services.ai_service import AIService


class AIProvider(Protocol):
    def analyze(self, metrics: dict, context: dict) -> dict: ...

    def get_metadata(self) -> dict: ...


class GeminiAIProvider:
    def __init__(self):
        self._service = AIService()

    def analyze(self, metrics: dict, context: dict) -> dict:
        return self._service.analyze(metrics, context)

    def get_metadata(self) -> dict:
        return self._service.get_metadata()
