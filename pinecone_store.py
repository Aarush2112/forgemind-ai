"""
pinecone_store.py — Pinecone + LlamaIndex vector store logic.

PDF loading strategy:
  1. Try PyMuPDF for text-based PDFs
  2. Fall back to docling with EasyOCR for scanned PDFs if PyMuPDF finds no text

Vector lifecycle:
  - index_documents(): append-only (Computer Vision and incremental uploads)
  - build_index(): rebuilds uploaded-document vectors only; preserves CV vectors
  - clear_index(): deletes all vectors (explicit user action)
"""

import json
import logging
import os
import re
import unicodedata
from pathlib import Path
from typing import Any, Dict, List, Tuple

logger = logging.getLogger(__name__)

from pinecone import Pinecone, ServerlessSpec
from llama_index.core import (
    VectorStoreIndex,
    SimpleDirectoryReader,
    StorageContext,
    Document,
)
from llama_index.vector_stores.pinecone import PineconeVectorStore

# ── Config ─────────────────────────────────────────────────────────────────────
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
PINECONE_INDEX   = os.getenv("PINECONE_INDEX", "rag-documents")
TMP_DIR          = "/tmp/rag_docs"
MAX_NON_LATIN    = 0.25
UPLOADED_SOURCE_TYPE = "uploaded_document"
CV_SOURCE_TYPES = {"computer_vision", "full_drawing"}
MAX_METADATA_STR_LEN = 2000

# ── Pinecone client ────────────────────────────────────────────────────────────
def _get_pinecone_index():
    pc = Pinecone(api_key=PINECONE_API_KEY)
    existing = [i.name for i in pc.list_indexes()]
    if PINECONE_INDEX not in existing:
        logger.info("Creating index '%s'...", PINECONE_INDEX)
        pc.create_index(
            name=PINECONE_INDEX,
            dimension=384,
            metric="cosine",
            spec=ServerlessSpec(cloud="aws", region="us-east-1"),
        )
    return pc.Index(PINECONE_INDEX)


# ── Text cleaner ───────────────────────────────────────────────────────────────
def _clean_doc_text(text: str) -> str | None:
    text = re.sub(r"\|W\|", " ", text)
    text = re.sub(r"\[Source\s*\d+\s*[—–-][^\]]*\]", "", text)
    text = text.encode("utf-8", errors="ignore").decode("utf-8")
    cleaned = []
    for ch in text:
        if unicodedata.category(ch) == "Cc" and ch not in ("\t", "\n"):
            cleaned.append(" ")
        else:
            cleaned.append(ch)
    text = re.sub(r" {2,}", " ", "".join(cleaned)).strip()
    if not text:
        return None
    non_latin = sum(1 for ch in text if ord(ch) > 0x024F and ch not in " \t\n\r")
    if len(text) > 0 and non_latin / len(text) > MAX_NON_LATIN:
        return None
    return text


# ── Docling PDF loader ─────────────────────────────────────────────────────────
def _load_pdf_docling(fpath: str) -> list[Document]:
    """
    Smart PDF loading:
    1. PyMuPDF first — fast, produces many chunks for text-based PDFs
    2. Docling + EasyOCR fallback — for scanned/image PDFs with no embedded text
    """
    fname = os.path.basename(fpath)

    # Try PyMuPDF first for text-based PDFs
    pymupdf_docs = _load_pdf_pymupdf(fpath)
    if pymupdf_docs:
        logger.info("'%s' → %d chunk(s) via PyMuPDF", fname, len(pymupdf_docs))
        return pymupdf_docs

    # No text found — scanned PDF, use docling + EasyOCR
    logger.info("No text in '%s', trying docling + EasyOCR", fname)

    # Fix SSL for macOS Python 3.14
    try:
        import ssl, certifi
        ssl._create_default_https_context = lambda: ssl.create_default_context(
            cafile=certifi.where()
        )
    except Exception:
        pass

    try:
        from docling.document_converter import DocumentConverter, PdfFormatOption
        from docling.datamodel.base_models import InputFormat
        from docling.datamodel.pipeline_options import PdfPipelineOptions

        ocr_options = None
        try:
            from docling.datamodel.pipeline_options import EasyOcrOptions
            ocr_options = EasyOcrOptions(force_full_page_ocr=True)
        except ImportError:
            pass

        pipeline_options = PdfPipelineOptions()
        pipeline_options.do_ocr = True
        if ocr_options:
            pipeline_options.ocr_options = ocr_options

        converter = DocumentConverter(
            format_options={
                InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)
            }
        )
        result    = converter.convert(fpath)
        doc_obj   = result.document
        full_text = doc_obj.export_to_markdown()

        if not full_text.strip():
            logger.warning("docling returned empty text for '%s'", fname)
            return []

        pages = _split_into_pages(doc_obj, full_text, fname, fpath)
        logger.info("'%s' → %d chunk(s) via docling+EasyOCR", fname, len(pages))
        return pages

    except Exception as e:
        logger.warning("docling failed on '%s': %s", fname, e)
        return []


def _split_into_pages(doc_obj, full_text: str, fname: str, fpath: str) -> list[Document]:
    """Split docling output into page-level chunks."""
    docs = []

    # Try page-level extraction from docling's item structure
    try:
        pages_text = {}
        for item, _ in doc_obj.iterate_items():
            prov = getattr(item, "prov", None)
            if prov:
                for p in prov:
                    pg = getattr(p, "page_no", None)
                    if pg is not None:
                        txt = getattr(item, "text", "") or ""
                        if txt.strip():
                            pages_text.setdefault(pg, []).append(txt.strip())

        if pages_text:
            for pg_num in sorted(pages_text.keys()):
                text = "\n".join(pages_text[pg_num])
                docs.append(Document(
                    text=text,
                    metadata={
                        "file_name":   fname,
                        "file_path":   fpath,
                        "page_label":  str(pg_num),
                        "page_number": pg_num,
                    }
                ))
            return docs
    except Exception:
        pass

    # Fallback: chunk the full markdown text into ~2000-char segments
    CHUNK = 2000
    for i, chunk in enumerate(
        [full_text[j:j+CHUNK] for j in range(0, len(full_text), CHUNK)], 1
    ):
        docs.append(Document(
            text=chunk,
            metadata={
                "file_name":   fname,
                "file_path":   fpath,
                "page_label":  str(i),
                "page_number": i,
            }
        ))
    return docs


# ── PyMuPDF fallback ───────────────────────────────────────────────────────────
def _load_pdf_pymupdf(fpath: str) -> list[Document]:
    """Fallback: PyMuPDF for text-based PDFs (no OCR)."""
    try:
        import pymupdf
    except ImportError:
        return []

    docs  = []
    fname = os.path.basename(fpath)
    pdf   = pymupdf.open(fpath)
    for page_num in range(pdf.page_count):
        text = pdf[page_num].get_text().strip()
        if text:
            docs.append(Document(
                text=text,
                metadata={
                    "file_name":   fname,
                    "file_path":   fpath,
                    "page_label":  str(page_num + 1),
                    "page_number": page_num + 1,
                }
            ))
    pdf.close()
    return docs


# ── Metadata helpers ───────────────────────────────────────────────────────────
def _sanitize_metadata(metadata: Dict[str, Any]) -> Dict[str, Any]:
    """
    Pinecone metadata must be scalar values (str, int, float, bool) or lists of str.
    Nested structures are JSON-encoded; long strings are truncated.
    """
    clean: Dict[str, Any] = {}
    for key, value in (metadata or {}).items():
        if value is None:
            continue
        if isinstance(value, bool):
            clean[key] = value
        elif isinstance(value, (int, float)):
            clean[key] = value
        elif isinstance(value, str):
            clean[key] = value[:MAX_METADATA_STR_LEN]
        elif isinstance(value, (list, tuple)):
            clean[key] = [
                str(item)[:MAX_METADATA_STR_LEN]
                for item in value
                if item is not None
            ]
        elif isinstance(value, dict):
            encoded = json.dumps(value, default=str)
            clean[key] = encoded[:MAX_METADATA_STR_LEN]
        else:
            clean[key] = str(value)[:MAX_METADATA_STR_LEN]
    return clean


def _delete_uploaded_document_vectors(pinecone_index) -> None:
    """Remove only uploaded-document vectors; preserve Computer Vision vectors."""
    try:
        pinecone_index.delete(
            filter={"source_type": {"$eq": UPLOADED_SOURCE_TYPE}}
        )
        logger.info(
            "Cleared uploaded-document vectors from '%s' (CV vectors preserved).",
            PINECONE_INDEX,
        )
    except Exception as exc:
        logger.warning(
            "Could not filter-delete uploaded vectors (%s); index may be empty.",
            exc,
        )


# ── Build index ────────────────────────────────────────────────────────────────
def build_index(documents_dir: str = TMP_DIR) -> VectorStoreIndex:
    pinecone_index = _get_pinecone_index()

    _delete_uploaded_document_vectors(pinecone_index)

    vector_store    = PineconeVectorStore(pinecone_index=pinecone_index)
    storage_context = StorageContext.from_defaults(vector_store=vector_store)

    clean_docs   = []
    skipped      = 0
    failed_files = []

    for fname in sorted(os.listdir(documents_dir)):
        fpath = os.path.join(documents_dir, fname)
        if not os.path.isfile(fpath):
            continue

        ext = Path(fname).suffix.lower()

        try:
            if ext == ".pdf":
                raw_docs = _load_pdf_docling(fpath)
                if not raw_docs:
                    failed_files.append(fname)
                    logger.warning("'%s' — no text extracted.", fname)
                    continue
            else:
                raw_docs = SimpleDirectoryReader(
                    input_files=[fpath], filename_as_id=True,
                ).load_data()
        except Exception as e:
            logger.error("ERROR loading '%s': %s", fname, e)
            skipped += 1
            continue

        for doc in raw_docs:
            if doc.text.strip().startswith("%PDF"):
                skipped += 1
                continue
            cleaned = _clean_doc_text(doc.text)
            if cleaned is None:
                skipped += 1
                continue
            meta = dict(doc.metadata or {})
            meta["source_type"] = UPLOADED_SOURCE_TYPE
            clean_docs.append(
                Document(text=cleaned, metadata=_sanitize_metadata(meta))
            )

    if skipped:
        logger.info("Skipped %d corrupt/empty chunks.", skipped)

    if not clean_docs:
        msg = "No usable text could be extracted from the uploaded documents."
        if failed_files:
            msg += "\nFailed files:\n  " + "\n  ".join(failed_files)
        raise ValueError(msg)

    logger.info("Indexing %d chunks into Pinecone...", len(clean_docs))
    logger.debug("Preview: %s", clean_docs[0].text[:200])

    return VectorStoreIndex.from_documents(clean_docs, storage_context=storage_context)


# ── Load existing index ────────────────────────────────────────────────────────
def load_index() -> VectorStoreIndex | None:
    try:
        pinecone_index = _get_pinecone_index()
        stats = pinecone_index.describe_index_stats()
        if stats.get("total_vector_count", 0) == 0:
            return None
        vector_store    = PineconeVectorStore(pinecone_index=pinecone_index)
        storage_context = StorageContext.from_defaults(vector_store=vector_store)
        return VectorStoreIndex.from_vector_store(vector_store, storage_context=storage_context)
    except Exception as e:
        logger.warning("Could not load index: %s", e)
        return None


# ── Utilities ──────────────────────────────────────────────────────────────────
def get_chunk_count() -> int:
    try:
        return _get_pinecone_index().describe_index_stats().get("total_vector_count", 0)
    except Exception:
        return 0


def clear_index():
    try:
        _get_pinecone_index().delete(delete_all=True)
        logger.info("Cleared all vectors from '%s'.", PINECONE_INDEX)
    except Exception as e:
        logger.warning("Could not clear index: %s", e)


# ── New function: index arbitrary documents ───────────────────────────────────
def index_documents(documents: List[Tuple[str, Dict[str, Any]]]) -> None:
    """
    Index a list of (text, metadata) tuples into the Pinecone index.
    Does not delete existing vectors.

    Args:
        documents: List of tuples (text, metadata) where text is the string to index
                  and metadata is a dictionary of metadata to attach.
    """
    if not documents:
        return

    pinecone_index = _get_pinecone_index()
    vector_store    = PineconeVectorStore(pinecone_index=pinecone_index)
    storage_context = StorageContext.from_defaults(vector_store=vector_store)

    docs_to_index = []
    for text, metadata in documents:
        cleaned = _clean_doc_text(text)
        if cleaned is not None and cleaned.strip():
            meta = _sanitize_metadata(metadata)
            if "source_type" not in meta:
                meta["source_type"] = "computer_vision"
            doc = Document(text=cleaned, metadata=meta)
            docs_to_index.append(doc)

    if not docs_to_index:
        logger.warning("No valid documents to index after cleaning.")
        return

    logger.info("Indexing %d documents from arbitrary source...", len(docs_to_index))
    VectorStoreIndex.from_documents(docs_to_index, storage_context=storage_context)
    logger.info("Finished indexing arbitrary documents.")