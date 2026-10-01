"""
UC14 GL Anomaly Detection Agent — Optional LLM Narrative
==============================================================
"""
from __future__ import annotations
import os


class LLMSummarizer:
    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY", "")
        self.enabled = bool(self.api_key)

    def summarize_run(self, decisions: list) -> str:
        return self._fallback_summary(decisions)

    @staticmethod
    def _fallback_summary(decisions: list) -> str:
        total = len(decisions)
        auto = sum(1 for d in decisions if d.action == "AUTO_RECONCILE")
        report = sum(1 for d in decisions if d.action == "DAILY_REPORT")
        investigate = sum(1 for d in decisions if d.action == "INVESTIGATE")
        return (
            f"Processed {total} GL postings.\n"
            f"  {auto} auto-reconciled — bank match confirmed, no action needed.\n"
            f"  {report} on the 7am daily exception report for AP/AR review.\n"
            f"  {investigate} escalated for immediate Finance Manager investigation."
        )
