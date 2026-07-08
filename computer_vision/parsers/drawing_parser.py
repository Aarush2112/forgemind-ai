"""
ForgeMind AI
Engineering Drawing Parser

Parses OCR text from complete engineering drawings.

Extracts:

- Drawing Number
- Drawing Title
- Revision
- Sheet Number
- Scale
- Date
- Company
- Project
- Client
"""

from __future__ import annotations

import re
from typing import Dict, List, Any


class DrawingParser:

    def __init__(self):

        self.patterns = {

            "drawing_number": [

                r"(?:Drawing\s*No\.?|DWG\s*No\.?)\s*[:\-]?\s*([A-Z0-9\-_\/]+)",

                r"\b[A-Z]{2,5}-\d{3,6}\b",

            ],

            "revision": [

                r"(?:Revision|Rev)\s*[:\-]?\s*([A-Z0-9]+)",

            ],

            "sheet": [

                r"(?:Sheet)\s*[:\-]?\s*(\d+\s*(?:of|/)\s*\d+)",

            ],

            "scale": [

                r"(?:Scale)\s*[:\-]?\s*([0-9:]+)",

            ],

            "date": [

                r"\b\d{2}[/-]\d{2}[/-]\d{2,4}\b",

                r"\b\d{4}[/-]\d{2}[/-]\d{2}\b",

            ],

            "project": [

                r"(?:Project)\s*[:\-]?\s*(.+)",

            ],

            "client": [

                r"(?:Client)\s*[:\-]?\s*(.+)",

            ]

        }

    # --------------------------------------------------

    def _find_first(self, text: str, regex_list: List[str]):

        for pattern in regex_list:

            match = re.search(pattern, text, re.IGNORECASE)

            if match:

                if match.lastindex:

                    return match.group(1).strip()

                return match.group().strip()

        return ""

    # --------------------------------------------------

    def parse(self, text: str) -> Dict[str, Any]:

        result = {

            "drawing_number": "",

            "title": "",

            "revision": "",

            "sheet": "",

            "scale": "",

            "date": "",

            "project": "",

            "client": ""

        }

        if not text:

            return result

        lines = [

            x.strip()

            for x in text.splitlines()

            if x.strip()

        ]

        if lines:

            result["title"] = lines[0]

        result["drawing_number"] = self._find_first(

            text,

            self.patterns["drawing_number"]

        )

        result["revision"] = self._find_first(

            text,

            self.patterns["revision"]

        )

        result["sheet"] = self._find_first(

            text,

            self.patterns["sheet"]

        )

        result["scale"] = self._find_first(

            text,

            self.patterns["scale"]

        )

        result["date"] = self._find_first(

            text,

            self.patterns["date"]

        )

        result["project"] = self._find_first(

            text,

            self.patterns["project"]

        )

        result["client"] = self._find_first(

            text,

            self.patterns["client"]

        )

        return result

    # --------------------------------------------------

    def to_text(self, drawing: Dict[str, Any]) -> str:

        text = []

        if drawing.get("title"):

            text.append(

                f"Drawing title is {drawing['title']}."

            )

        if drawing.get("drawing_number"):

            text.append(

                f"Drawing number {drawing['drawing_number']}."

            )

        if drawing.get("revision"):

            text.append(

                f"Revision {drawing['revision']}."

            )

        if drawing.get("sheet"):

            text.append(

                f"Sheet {drawing['sheet']}."

            )

        if drawing.get("scale"):

            text.append(

                f"Scale {drawing['scale']}."

            )

        if drawing.get("date"):

            text.append(

                f"Date {drawing['date']}."

            )

        if drawing.get("project"):

            text.append(

                f"Project {drawing['project']}."

            )

        if drawing.get("client"):

            text.append(

                f"Client {drawing['client']}."

            )

        return " ".join(text)

    # --------------------------------------------------

    def summary(self, drawing: Dict[str, Any]) -> Dict[str, str]:

        return {

            "drawing_number": drawing.get(

                "drawing_number",

                ""

            ),

            "title": drawing.get(

                "title",

                ""

            ),

            "revision": drawing.get(

                "revision",

                ""

            ),

            "project": drawing.get(

                "project",

                ""

            )

        }