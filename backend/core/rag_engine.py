"""
Regulatory & Corporate Disclosure RAG Engine
Provides semantic chunking, grounded document retrieval, and visible citation attribution for SEBI filings.
"""

import os
import re
import math
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

SEBI_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "sebi_filings")

@dataclass
class DocumentChunk:
    doc_id: str
    company_symbol: str
    company_name: str
    filing_type: str
    date: str
    section_title: str
    paragraph_num: int
    content: str
    source_tag: str

@dataclass
class RAGQueryResult:
    chunk: DocumentChunk
    relevance_score: float
    citation_text: str

class RAGEngine:
    def __init__(self, doc_dir: str = SEBI_DIR):
        self.doc_dir = doc_dir
        self.chunks: List[DocumentChunk] = []
        self._build_index()

    def _build_index(self):
        """Loads and chunks all SEBI filings from disk."""
        self.chunks.clear()
        if not os.path.exists(self.doc_dir):
            return

        for filename in os.listdir(self.doc_dir):
            if filename.endswith(".txt"):
                filepath = os.path.join(self.doc_dir, filename)
                with open(filepath, "r", encoding="utf-8") as f:
                    text = f.read()
                self._parse_and_chunk_file(text, filename)

    def _parse_and_chunk_file(self, text: str, filename: str):
        lines = text.strip().split("\n")
        doc_id = "SEBI-DOC-UNKNOWN"
        company_symbol = ""
        company_name = ""
        filing_type = "Regulatory Disclosure"
        date_str = "2025-Q3"
        section_title = "General"

        header_lines = []
        content_lines = []
        is_header = True

        for line in lines:
            if is_header and line.startswith("[DOCUMENT_ID:"):
                doc_id = line.replace("[DOCUMENT_ID:", "").replace("]", "").strip()
            elif is_header and line.startswith("COMPANY:"):
                comp_raw = line.replace("COMPANY:", "").strip()
                match = re.search(r"NSE:\s*([A-Za-z0-9_]+)", comp_raw)
                company_symbol = match.group(1).upper() if match else comp_raw.split()[0].upper()
                company_name = comp_raw.split("(")[0].strip()
            elif is_header and line.startswith("FILING_TYPE:"):
                filing_type = line.replace("FILING_TYPE:", "").strip()
            elif is_header and line.startswith("DATE:"):
                date_str = line.replace("DATE:", "").strip()
            elif is_header and line.startswith("SECTION:"):
                section_title = line.replace("SECTION:", "").strip()
                is_header = False
            else:
                if line.strip():
                    content_lines.append(line)

        full_content = "\n".join(content_lines)
        paragraphs = re.split(r"\n(?=\d+\.\s+)", full_content)

        for i, para in enumerate(paragraphs, 1):
            cleaned_para = para.strip()
            if len(cleaned_para) > 30:
                first_line = cleaned_para.split("\n")[0]
                sub_section = first_line.split(":")[0].strip() if ":" in first_line else f"Para {i}"
                source_tag = f"[{company_symbol} SEBI Filing {date_str} § {sub_section}]"
                
                chunk = DocumentChunk(
                    doc_id=doc_id,
                    company_symbol=company_symbol,
                    company_name=company_name,
                    filing_type=filing_type,
                    date=date_str,
                    section_title=f"{section_title} > {sub_section}",
                    paragraph_num=i,
                    content=cleaned_para,
                    source_tag=source_tag
                )
                self.chunks.append(chunk)

    def query(self, symbol: str, query_text: str, top_k: int = 3) -> List[RAGQueryResult]:
        if not self.chunks:
            return []

        symbol_upper = symbol.upper()
        relevant_chunks = [c for c in self.chunks if c.company_symbol == symbol_upper]
        if not relevant_chunks:
            relevant_chunks = self.chunks

        query_tokens = set(re.findall(r"\w+", query_text.lower()))
        results: List[RAGQueryResult] = []

        for chunk in relevant_chunks:
            chunk_tokens = re.findall(r"\w+", chunk.content.lower()) + re.findall(r"\w+", chunk.section_title.lower())
            if not chunk_tokens:
                continue

            chunk_set = set(chunk_tokens)
            intersection = query_tokens.intersection(chunk_set)
            
            boost = 1.0
            for keyword in ["debt", "ebitda", "margin", "capex", "revenue", "arpu", "dividend", "order", "guidance", "profit"]:
                if keyword in query_tokens and keyword in chunk_set:
                    boost += 0.35

            score = (len(intersection) / (math.sqrt(len(query_tokens) + 1) * math.sqrt(len(chunk_set) + 1))) * boost
            score = min(0.99, max(0.20, score * 3.5))

            citation = f"{chunk.source_tag} — {chunk.doc_id}"
            results.append(RAGQueryResult(chunk=chunk, relevance_score=round(score, 3), citation_text=citation))

        results.sort(key=lambda x: x.relevance_score, reverse=True)
        return results[:top_k]

    def get_all_indexed_symbols(self) -> List[str]:
        return list(set(c.company_symbol for c in self.chunks if c.company_symbol))
