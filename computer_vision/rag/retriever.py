"""
ForgeMind AI
RAG Retriever

Retrieves relevant context from Pinecone using
the existing LlamaIndex retriever.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List

from pinecone_store import load_index

logger = logging.getLogger(__name__)


class RAGRetriever:

    """
    Wrapper around the existing Pinecone + LlamaIndex retriever.

    Used by the chatbot after Computer Vision indexing.
    """

    def __init__(
        self,
        top_k: int = 10,
    ):

        self.top_k = top_k

        self.index = load_index()

        self.retriever = None

        if self.index:

            self.retriever = self.index.as_retriever(
                similarity_top_k=top_k
            )

    # ------------------------------------------------------

    def reload(self):
        self.index = load_index()
        if self.index:
            self.retriever = self.index.as_retriever(
                similarity_top_k=self.top_k
            )
        else:
            self.retriever = None
        logger.info("RAG retriever reloaded (ready=%s)", self.is_ready())

    # ------------------------------------------------------

    def search(
        self,
        query: str,
    ) -> List[Any]:

        if self.retriever is None:

            return []

        try:

            return self.retriever.retrieve(query)

        except Exception:
            logger.exception("Retriever search failed for query: %s", query[:120])
            return []

    # ------------------------------------------------------

    def context(
        self,
        query: str,
    ) -> str:

        nodes = self.search(query)

        context = []

        for node in nodes:

            try:

                text = node.node.get_content()

                if text:

                    context.append(text)

            except Exception:

                continue

        return "\n\n".join(context)

    # ------------------------------------------------------

    def sources(
        self,
        query: str,
    ) -> List[Dict[str, Any]]:

        nodes = self.search(query)

        results = []

        for node in nodes:

            try:

                metadata = node.node.metadata or {}

                results.append({
                    "score": float(node.score or 0),
                    "file_name": (
                        metadata.get("file_name")
                        or metadata.get("image_name")
                    ),
                    "source_type": metadata.get("source_type"),
                    "source": metadata.get("source"),
                    "image": metadata.get("image") or metadata.get("image_name"),
                    "label": metadata.get("label") or metadata.get("symbol_class"),
                    "page": metadata.get("page_label"),
                })

            except Exception:

                continue

        return results

    # ------------------------------------------------------

    def ask(
        self,
        query: str,
    ) -> Dict[str, Any]:

        nodes = self.search(query)

        context = []

        references = []

        for node in nodes:

            try:

                context.append(

                    node.node.get_content()

                )

                references.append(

                    node.node.metadata

                )

            except Exception:

                continue

        return {

            "query": query,

            "context": "\n\n".join(context),

            "references": references,

            "count": len(context),

        }

    # ------------------------------------------------------

    def is_ready(self) -> bool:

        return self.retriever is not None