"""RAG retriever that combines semantic search with keyword grep."""

from __future__ import annotations

from vidya_copilot.rag.indexer import CodebaseIndexer


class CodeRetriever:
    def __init__(self, indexer: CodebaseIndexer) -> None:
        self.indexer = indexer

    def retrieve(self, query: str, top_k: int = 8) -> str:
        semantic = self.indexer.search(query, top_k=top_k)
        if not semantic:
            return "No indexed code found. Run POST /api/codebase/index first."

        parts = [f"## Relevant code for: {query}\n"]
        for i, hit in enumerate(semantic, 1):
            parts.append(
                f"### [{i}] {hit['source']} (score: {hit['score']:.3f})\n"
                f"```\n{hit['content']}\n```\n"
            )
        return "\n".join(parts)

    def answer_about_codebase(self, question: str) -> str:
        symbol_hints = self._extract_symbols(question)
        grep_results: list[dict] = []
        for symbol in symbol_hints:
            grep_results.extend(self.indexer.find_symbol_usage(symbol))

        context = self.retrieve(question)
        if grep_results:
            context += "\n\n## Exact symbol matches\n"
            for m in grep_results[:20]:
                context += f"- `{m['file']}:{m['line']}` — {m['content']}\n"
        return context

    def _extract_symbols(self, question: str) -> list[str]:
        import re
        candidates = re.findall(r"[A-Z][a-zA-Z0-9]+(?:Page|Client|Test|Helper|Fixture)?", question)
        quoted = re.findall(r"['\"]([^'\"]+)['\"]", question)
        return list({*candidates, *quoted})[:5]
