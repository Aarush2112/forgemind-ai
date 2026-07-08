"""
ForgeMind AI
P&ID Parser

Converts OCR text into structured engineering entities.

Extracts:
- Equipment Tags
- Instrument Tags
- Line Numbers
- Services
- Pressure
- Temperature
- Flow
"""

from __future__ import annotations

import re
from dataclasses import dataclass, asdict
from typing import Dict, List


# =====================================================
# Data Classes
# =====================================================

@dataclass
class Equipment:

    tag: str
    equipment_type: str


@dataclass
class Instrument:

    tag: str
    instrument_type: str


@dataclass
class Line:

    line_number: str


@dataclass
class Measurement:

    measurement_type: str
    value: str


# =====================================================
# Parser
# =====================================================

class PidParser:

    def __init__(self):

        self.equipment_patterns = {

            "Pump":
                re.compile(r"\bP[- ]?\d{2,5}\b", re.IGNORECASE),

            "Valve":
                re.compile(r"\bV[- ]?\d{2,5}\b", re.IGNORECASE),

            "HeatExchanger":
                re.compile(r"\bHX[- ]?\d{2,5}\b", re.IGNORECASE),

            "Tank":
                re.compile(r"\bTK[- ]?\d{2,5}\b", re.IGNORECASE),

            "Compressor":
                re.compile(r"\bC[- ]?\d{2,5}\b", re.IGNORECASE),

        }

        self.instrument_patterns = {

            "Pressure Gauge":
                re.compile(r"\bPG[- ]?\d{2,5}\b", re.IGNORECASE),

            "Pressure Indicator":
                re.compile(r"\bPI[- ]?\d{2,5}\b", re.IGNORECASE),

            "Temperature Indicator":
                re.compile(r"\bTI[- ]?\d{2,5}\b", re.IGNORECASE),

            "Flow Indicator":
                re.compile(r"\bFI[- ]?\d{2,5}\b", re.IGNORECASE),

            "Level Indicator":
                re.compile(r"\bLI[- ]?\d{2,5}\b", re.IGNORECASE),

            "Pressure Transmitter":
                re.compile(r"\bPT[- ]?\d{2,5}\b", re.IGNORECASE),

            "Flow Transmitter":
                re.compile(r"\bFT[- ]?\d{2,5}\b", re.IGNORECASE),

            "Temperature Transmitter":
                re.compile(r"\bTT[- ]?\d{2,5}\b", re.IGNORECASE),

        }

        self.line_pattern = re.compile(

            r"\b\d{2,6}[-/][A-Z0-9-]+\b",

            re.IGNORECASE,

        )

        self.pressure_pattern = re.compile(

            r"\d+(\.\d+)?\s?(bar|psi|kpa|mpa)",

            re.IGNORECASE,

        )

        self.temperature_pattern = re.compile(

            r"\d+(\.\d+)?\s?(c|°c|f|°f)",

            re.IGNORECASE,

        )

        self.flow_pattern = re.compile(

            r"\d+(\.\d+)?\s?(l/min|m3/h|kg/h)",

            re.IGNORECASE,

        )

    # =================================================

    def parse(

        self,

        text: str,

    ) -> Dict:

        result = {

            "equipment": [],

            "instruments": [],

            "lines": [],

            "measurements": [],

        }

        if not text:

            return result

        # ------------------------------------------

        for equipment, pattern in self.equipment_patterns.items():

            matches = pattern.findall(text)

            for match in matches:

                result["equipment"].append(

                    Equipment(

                        tag=match.upper(),

                        equipment_type=equipment,

                    )

                )

        # ------------------------------------------

        for instrument, pattern in self.instrument_patterns.items():

            matches = pattern.findall(text)

            for match in matches:

                result["instruments"].append(

                    Instrument(

                        tag=match.upper(),

                        instrument_type=instrument,

                    )

                )

        # ------------------------------------------

        for match in self.line_pattern.findall(text):

            result["lines"].append(

                Line(

                    line_number=match,

                )

            )

        # ------------------------------------------

        for match in self.pressure_pattern.finditer(text):

            result["measurements"].append(

                Measurement(

                    "Pressure",

                    match.group(),

                )

            )

        for match in self.temperature_pattern.finditer(text):

            result["measurements"].append(

                Measurement(

                    "Temperature",

                    match.group(),

                )

            )

        for match in self.flow_pattern.finditer(text):

            result["measurements"].append(

                Measurement(

                    "Flow",

                    match.group(),

                )

            )

        return {

            "equipment":

                [

                    asdict(x)

                    for x in result["equipment"]

                ],

            "instruments":

                [

                    asdict(x)

                    for x in result["instruments"]

                ],

            "lines":

                [

                    asdict(x)

                    for x in result["lines"]

                ],

            "measurements":

                [

                    asdict(x)

                    for x in result["measurements"]

                ],

        }

    # =================================================

    def to_text(

        self,

        parsed: Dict,

    ) -> str:

        output = []

        for eq in parsed.get("equipment", []):

            output.append(

                f"{eq['equipment_type']} {eq['tag']}"

            )

        for ins in parsed.get("instruments", []):

            output.append(

                f"{ins['instrument_type']} {ins['tag']}"

            )

        for line in parsed.get("lines", []):

            output.append(

                f"Line {line['line_number']}"

            )

        for measurement in parsed.get("measurements", []):

            output.append(

                f"{measurement['measurement_type']} {measurement['value']}"

            )

        return ". ".join(output)

    # =================================================

    def extract_tags(

        self,

        text: str,

    ) -> List[str]:

        parsed = self.parse(text)

        tags = []

        for eq in parsed["equipment"]:

            tags.append(eq["tag"])

        for ins in parsed["instruments"]:

            tags.append(ins["tag"])

        return tags

    # =================================================

    def extract_equipment(

        self,

        text: str,

    ) -> List[str]:

        parsed = self.parse(text)

        return [

            x["equipment_type"]

            for x in parsed["equipment"]

        ]