"""
ForgeMind AI
RAG Indexer

Converts OCR + Parser output into documents that can be indexed into
Pinecone using the existing pinecone_store.py.

Author: ForgeMind AI
"""

from __future__ import annotations

from typing import Dict, Any, List, Tuple

from pinecone_store import index_documents


class RAGIndexer:

    """
    Converts Computer Vision output into Pinecone documents.
    """

    def __init__(self):

        self.documents: List[Tuple[str, Dict[str, Any]]] = []

    # -----------------------------------------------------

    def reset(self):

        self.documents.clear()

    # -----------------------------------------------------

    def add_detection(

        self,

        image_name: str,

        detection: Dict[str, Any],

    ) -> None:

        chunks = []

        label = detection.get("label", "")

        confidence = detection.get("confidence", 0)

        bbox = detection.get("bbox", {})

        ocr = detection.get("ocr", "")

        if label:

            chunks.append(f"Detected Equipment: {label}")

        if ocr:

            chunks.append(f"OCR Text: {ocr}")

        pid = detection.get("pid")

        if pid:

            chunks.append(str(pid))

        table = detection.get("table")

        if table:

            chunks.append(str(table))

        drawing = detection.get("drawing")

        if drawing:

            chunks.append(str(drawing))

        text = "\n".join(chunks)

        metadata = {

            "source": "computer_vision",

            "image": image_name,

            "label": label,

            "confidence": confidence,

            "bbox": bbox,

        }

        self.documents.append(

            (

                text,

                metadata,

            )

        )

    # -----------------------------------------------------

    def add_full_drawing(

        self,

        image_name: str,

        drawing: Dict[str, Any],

        table: Dict[str, Any],

        pid: Dict[str, Any],

        full_text: str,

    ):

        chunks = []

        if drawing:

            chunks.append(str(drawing))

        if table:

            chunks.append(str(table))

        if pid:

            chunks.append(str(pid))

        if full_text:

            chunks.append(full_text)

        metadata = {

            "source": "drawing",

            "image": image_name,

        }

        self.documents.append(

            (

                "\n".join(chunks),

                metadata,

            )

        )

    # -----------------------------------------------------

    def build(self):

        unique = {}

        for text, metadata in self.documents:

            key = text.strip().lower()

            if not key:

                continue

            unique[key] = (text, metadata)

        self.documents = list(unique.values())

    # -----------------------------------------------------

    def upload(self):

        self.build()

        if not self.documents:

            return

        index_documents(

            self.documents

        )

    # -----------------------------------------------------

    def count(self):

        return len(self.documents)