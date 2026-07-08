"""
ForgeMind AI
OCR Text Cleaner

Normalizes OCR output before parsing and indexing.

Responsibilities
----------------
- Remove OCR noise
- Fix common OCR mistakes
- Normalize whitespace
- Standardize engineering tags
- Preserve equipment identifiers
"""

from __future__ import annotations

import re
from typing import List


class OCRTextCleaner:

    def __init__(self):

        self.character_replacements = {

            "—": "-",
            "–": "-",
            "_": "-",
            "|": "I",
            "§": "S",
            "¢": "C",
            "€": "E",
            "°": "0",
            "•": "",
            "·": "",
            "`": "",
            "'": "",
            '"': "",

        }

    # ------------------------------------------------

    def normalize_whitespace(
        self,
        text: str,
    ) -> str:

        text = text.replace("\n", " ")

        text = re.sub(r"\s+", " ", text)

        return text.strip()

    # ------------------------------------------------

    def replace_characters(
        self,
        text: str,
    ) -> str:

        for old, new in self.character_replacements.items():

            text = text.replace(old, new)

        return text

    # ------------------------------------------------

    def normalize_tags(
        self,
        text: str,
    ) -> str:

        text = re.sub(

            r"P[\s\-]*([0-9]{2,4})",

            r"P-\1",

            text,

            flags=re.IGNORECASE,

        )

        text = re.sub(

            r"V[\s\-]*([0-9]{2,4})",

            r"V-\1",

            text,

            flags=re.IGNORECASE,

        )

        text = re.sub(

            r"PG[\s\-]*([0-9]{2,4})",

            r"PG-\1",

            text,

            flags=re.IGNORECASE,

        )

        text = re.sub(

            r"HX[\s\-]*([0-9]{2,4})",

            r"HX-\1",

            text,

            flags=re.IGNORECASE,

        )

        return text

    # ------------------------------------------------

    def remove_noise(
        self,
        text: str,
    ) -> str:

        text = re.sub(

            r"[^A-Za-z0-9\-\.\,\:\(\)\/ ]",

            " ",

            text,

        )

        return text

    # ------------------------------------------------

    def fix_common_ocr_errors(
        self,
        text: str,
    ) -> str:

        replacements = {

            "O": "0",

            "l": "1",

            "I": "1",

        }

        words = text.split()

        fixed_words = []

        for word in words:

            if any(c.isdigit() for c in word):

                for old, new in replacements.items():

                    word = word.replace(old, new)

            fixed_words.append(word)

        return " ".join(fixed_words)

    # ------------------------------------------------

    def clean(
        self,
        text: str,
    ) -> str:

        if not text:

            return ""

        text = self.replace_characters(text)

        text = self.remove_noise(text)

        text = self.normalize_whitespace(text)

        text = self.fix_common_ocr_errors(text)

        text = self.normalize_tags(text)

        text = self.normalize_whitespace(text)

        return text

    # ------------------------------------------------

    def clean_lines(
        self,
        lines: List[str],
    ) -> List[str]:

        cleaned = []

        for line in lines:

            line = self.clean(line)

            if line:

                cleaned.append(line)

        return cleaned


cleaner = OCRTextCleaner()