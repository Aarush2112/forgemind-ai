from typing import List, Optional

from pydantic import BaseModel


class BoundingBox(BaseModel):
    x1: int
    y1: int
    x2: int
    y2: int


class DetectedSymbol(BaseModel):
    label: str
    confidence: float
    bounding_box: BoundingBox


class LayoutBlock(BaseModel):
    block_type: str
    bounding_box: BoundingBox


class TableCell(BaseModel):
    row: int
    column: int
    text: str


class ParsedEquipment(BaseModel):
    equipment_type: str
    equipment_id: str


class ComputerVisionResult(BaseModel):
    text: Optional[str] = None

    layout: List[LayoutBlock] = []

    tables: List[TableCell] = []

    symbols: List[DetectedSymbol] = []

    equipment: List[ParsedEquipment] = []