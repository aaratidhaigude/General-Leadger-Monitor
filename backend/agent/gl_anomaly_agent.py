"""
UC14 GL Anomaly Detection Agent — Main Orchestrator
=========================================================
Perceive → Reason → Act → Learn Loop
"""
from __future__ import annotations
import os, sys
from typing import Optional

from backend.agent.data_loader import UC14DataLoader
from backend.agent.scoring_engine import ScoringEngine, GLAnomalyDecision
from backend.agent.output_writer import ResultsWriter
from backend.agent.llm_summary import LLMSummarizer


class GLAnomalyAgent:

    def __init__(self, use_llm: bool = False, excel_path: str = None):
        self.use_llm = use_llm
        self.loader = UC14DataLoader(excel_path)
        self.engine = ScoringEngine()
        self.writer = ResultsWriter()
        self.summarizer = LLMSummarizer() if use_llm else None

    def run_all(self) -> list[GLAnomalyDecision]:
        self.loader.load()
        results = [self._process(p.doc_no, p.line_item) for p in self.loader.postings]
        results = [r for r in results if r]
        self.writer.write_results(results)
        self._print_summary(results)
        return results

    def run_posting(self, doc_no: str, line_item: str) -> Optional[GLAnomalyDecision]:
        self.loader.load()
        result = self._process(doc_no, line_item)
        if result:
            self.writer.write_results([result])
            self._print_single(result, verbose=True)
        else:
            print(f"[Agent] Posting {doc_no}/{line_item} not found.")
        return result

    def _process(self, doc_no: str, line_item: str) -> Optional[GLAnomalyDecision]:
        posting = self.loader.get_posting(doc_no, line_item)
        if posting is None:
            return None
        baseline = self.loader.get_baseline(posting.gl_account, posting.doc_type)
        bank_entry = self.loader.get_bank_entry(posting.utr_reference) if posting.utr_reference else None
        return self.engine.score_posting(posting, baseline, bank_entry)

    def _print_single(self, d: GLAnomalyDecision, verbose: bool = False):
        print(f"\n{d.doc_no}/{d.line_item}  {d.gl_account} ({d.doc_type})  \u20b9{d.amount_inr:,.0f}")
        print(f"  ARI={d.ari:.1f}  ->  {d.action}")
        if verbose:
            print(f"  Justification: {d.justification}")
            print(f"  SAP action: {d.sap_action}")
            print(f"  Audit ref: {d.audit_trail_ref}")

    def _print_summary(self, results: list[GLAnomalyDecision]):
        summary = LLMSummarizer._fallback_summary(results)
        print("\n" + "=" * 65)
        print("  SAP Vendor Intelligence & AP Risk Agent (VIRA) — Run Summary")
        print("=" * 65)
        print(summary)
        print("=" * 60)


if __name__ == "__main__":
    agent = GLAnomalyAgent()
    agent.run_all()
