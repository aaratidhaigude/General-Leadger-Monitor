"""
RAG Engine & LLM Vector Auditing System (Ollama Embedding API + Local Model Fallback)
========================================================================================
Ingests official SAP Procurement Documents & Contracts from data/contracts/ and data/sap_docs/.
Indices vector embeddings and performs RAG + LLM clause & PO/GR/IR retrieval.
Supports Ollama Embeddings API (http://localhost:11434/api/embeddings - qwen / nomic-embed-text) with automatic local fallback.
"""
from __future__ import annotations
import os, glob, json
from dataclasses import dataclass
from typing import Optional, List

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False

try:
    from sentence_transformers import SentenceTransformer
    import numpy as np
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CONTRACTS_DIR = os.path.join(BASE_DIR, "data", "contracts")
SAP_DOCS_DIR = os.path.join(BASE_DIR, "data", "sap_docs")
OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://localhost:11434/api/embeddings")
OLLAMA_MODEL = os.environ.get("OLLAMA_EMBED_MODEL", "qwen2.5")

@dataclass
class ContractChunk:
    contract_ref: str
    vendor_name: str
    clause_title: str
    content: str
    doc_type: str = "CONTRACT" # CONTRACT | PO | GR | IR
    score: float = 0.0

class VendorRAGEngine:
    def __init__(self):
        self.chunks: List[ContractChunk] = []
        self.embeddings = None
        self.local_model = None
        self.use_ollama = False
        self._initialize_vector_store()

    def _get_ollama_embedding(self, text: str) -> Optional[List[float]]:
        if not REQUESTS_AVAILABLE:
            return None
        try:
            resp = requests.post(
                OLLAMA_URL,
                json={"model": OLLAMA_MODEL, "prompt": text},
                timeout=2.0
            )
            if resp.status_code == 200:
                return resp.json().get("embedding")
        except Exception:
            pass
        return None

    def _initialize_vector_store(self):
        os.makedirs(CONTRACTS_DIR, exist_ok=True)
        os.makedirs(SAP_DOCS_DIR, exist_ok=True)
        
        # Load Contract Outline Agreements (ME33K)
        contract_files = glob.glob(os.path.join(CONTRACTS_DIR, "*.txt"))
        # Load SAP PO/GR/IR Transaction Documents (ME23N / MIGO / MIRO)
        sap_doc_files = glob.glob(os.path.join(SAP_DOCS_DIR, "*.txt"))

        all_files = [(f, "CONTRACT") for f in contract_files] + [(f, "SAP_TRANSACTION") for f in sap_doc_files]

        for filepath, doc_category in all_files:
            filename = os.path.basename(filepath)
            contract_ref = filename.replace(".txt", "")
            
            with open(filepath, "r", encoding="utf-8") as f:
                text = f.read()
            
            sections = text.split("SECTION ") if "SECTION " in text else text.split("================================================================================")
            for sec in sections:
                if not sec.strip():
                    continue
                lines = sec.strip().splitlines()
                title = lines[0] if lines else "SAP Document Clause"
                
                vendor_name = "Tata Consultancy Services Ltd" if "TATA" in contract_ref or "TCS" in text else \
                              "Infosys BPM Limited" if "INFOSYS" in contract_ref or "Infosys" in text else \
                              "Wipro Enterprises Pvt Ltd" if "WIPRO" in contract_ref or "Wipro" in text else \
                              "HCL Technologies Ltd"
                
                self.chunks.append(ContractChunk(
                    contract_ref=contract_ref,
                    vendor_name=vendor_name,
                    clause_title=title[:60],
                    content=sec.strip(),
                    doc_type=doc_category
                ))

        # Test Ollama API availability first
        test_emb = self._get_ollama_embedding("test contract embedding")
        if test_emb is not None:
            self.use_ollama = True
            print(f"[RAG] Connected to live Ollama Embedding API ({OLLAMA_MODEL}) at {OLLAMA_URL}")
        elif SENTENCE_TRANSFORMERS_AVAILABLE and self.chunks:
            try:
                self.local_model = SentenceTransformer("all-MiniLM-L6-v2")
                texts = [f"{c.clause_title} {c.content}" for c in self.chunks]
                self.embeddings = self.local_model.encode(texts, convert_to_numpy=True)
                print(f"[RAG] Vector Embeddings engine initialized with {len(self.chunks)} SAP contract & document chunks (all-MiniLM-L6-v2)")
            except Exception as e:
                print(f"[RAG] Warning: Vector embeddings fallback mode ({e})")

    def query_contract_clauses(self, vendor_name: str, query_text: str, top_k: int = 2) -> List[ContractChunk]:
        """
        RAG Retrieval: Finds relevant SAP contract chunks or transaction records for a given vendor and query.
        """
        matching_chunks = [c for c in self.chunks if vendor_name.lower() in c.vendor_name.lower() or c.vendor_name.lower() in vendor_name.lower()]
        if not matching_chunks:
            matching_chunks = self.chunks

        # Option A: Try Ollama Embeddings API if live
        if self.use_ollama:
            q_emb = self._get_ollama_embedding(query_text)
            if q_emb is not None:
                scores = []
                for c in matching_chunks:
                    c_emb = self._get_ollama_embedding(f"{c.clause_title} {c.content}")
                    if c_emb is not None and len(c_emb) == len(q_emb):
                        dot = sum(a * b for a, b in zip(q_emb, c_emb))
                        scores.append(dot)
                    else:
                        scores.append(0.5)
                top_indices = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:top_k]
                results = []
                for idx in top_indices:
                    chunk = matching_chunks[idx]
                    chunk.score = float(scores[idx])
                    results.append(chunk)
                return results

        # Option B: Local Vector Model Search
        if self.local_model is not None and self.embeddings is not None:
            try:
                q_emb = self.local_model.encode([query_text], convert_to_numpy=True)
                indices = [self.chunks.index(c) for c in matching_chunks]
                sub_embs = self.embeddings[indices]
                sims = np.dot(sub_embs, q_emb.T).squeeze()
                
                if isinstance(sims, (int, float, np.float32, np.float64)):
                    sims = np.array([sims])

                top_indices = np.argsort(sims)[::-1][:top_k]
                results = []
                for idx in top_indices:
                    chunk = matching_chunks[idx]
                    chunk.score = float(sims[idx])
                    results.append(chunk)
                return results
            except Exception:
                pass
        
        # Option C: Keyword Fallback
        for c in matching_chunks:
            c.score = 0.85 if any(w in c.content.lower() for w in query_text.lower().split()) else 0.4
        return matching_chunks[:top_k]

# Global Singleton RAG Engine
rag_singleton = VendorRAGEngine()
