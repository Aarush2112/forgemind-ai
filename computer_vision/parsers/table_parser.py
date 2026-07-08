"""
ForgeMind AI
Industrial Table Parser

Parses engineering tables extracted from OCR.

Supports

- Equipment Schedule
- Instrument Index
- Bill of Materials
- Valve Schedule
- Pump List
- Generic Tables
"""

from __future__ import annotations

import re
from typing import Any, Dict, List


class TableParser:

    def __init__(self):

        self.column_splitter = re.compile(r"\s{2,}|\t|\|")

    # -------------------------------------------------

    def clean_line(self, line: str) -> str:

        line = re.sub(r"\s+", " ", line)

        return line.strip()

    # -------------------------------------------------

    def split_row(self, line: str) -> List[str]:

        cols = self.column_splitter.split(line)

        cols = [

            c.strip()

            for c in cols

            if c.strip()

        ]

        if len(cols) <= 1:

            cols = [

                c.strip()

                for c in line.split()

                if c.strip()

            ]

        return cols

    # -------------------------------------------------

    def parse(

        self,

        text: str,

    ) -> Dict[str, Any]:

        table = {

            "headers": [],

            "rows": [],

            "row_count": 0,

            "column_count": 0,

        }

        if not text:

            return table

        lines = [

            self.clean_line(x)

            for x in text.splitlines()

            if x.strip()

        ]

        if not lines:

            return table

        headers = self.split_row(lines[0])

        table["headers"] = headers

        table["column_count"] = len(headers)

        for line in lines[1:]:

            row = self.split_row(line)

            if not row:

                continue

            while len(row) < len(headers):

                row.append("")

            row = row[: len(headers)]

            table["rows"].append(row)

        table["row_count"] = len(table["rows"])

        return table

    # -------------------------------------------------

    def to_text(

        self,

        parsed: Dict[str, Any],

    ) -> str:

        if not parsed["headers"]:

            return ""

        text = []

        text.append(

            f"Engineering table containing {parsed['row_count']} rows."

        )

        text.append(

            "Columns: "

            + ", ".join(parsed["headers"])

            + "."

        )

        for idx, row in enumerate(parsed["rows"][:5]):

            values = []

            for h, v in zip(parsed["headers"], row):

                if v:

                    values.append(

                        f"{h} = {v}"

                    )

            if values:

                text.append(

                    f"Row {idx+1}: "

                    + ", ".join(values)

                    + "."

                )

        if parsed["row_count"] > 5:

            text.append(

                f"{parsed['row_count']-5} additional rows."

            )

        return " ".join(text)

    # -------------------------------------------------

    def extract_equipment_tags(

        self,

        parsed: Dict[str, Any],

    ) -> List[str]:

        tags = []

        regex = re.compile(

            r"[A-Z]{1,3}-?\d{2,5}",

            re.IGNORECASE,

        )

        for row in parsed["rows"]:

            for value in row:

                tags.extend(

                    regex.findall(value)

                )

        return list(set(tags))