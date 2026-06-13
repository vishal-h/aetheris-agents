from dataclasses import dataclass
from typing import Optional


@dataclass
class PlanComponent:
    code: str           # raw code from drawing, e.g. "DB30", "BLB42FHL", "W2739"
    drawing: str        # source drawing label, e.g. "floor_plan", "El1", "El2"
    qty: int            # default 1; incremented when same code appears multiple times
    notes: Optional[str]  # any annotation text captured near the component


@dataclass
class CatalogItem:
    sku: str              # full SKU incl. color code, e.g. "3DB30-2004"
    series: str           # "2000", "3000", etc.
    color_code: str       # "2001", "2004", etc.
    color_name: str       # "Ivory White", "Mingo Oak"
    description: str      # full description from catalog
    cabinet_type: str     # "Base Cabinet", "Wall Cabinet", "Accessory", etc.
    width_in: Optional[float]
    height_in: Optional[float]
    depth_in: Optional[float]
    msrp: float


@dataclass
class ResolvedItem:
    component: PlanComponent
    catalog_item: Optional[CatalogItem]   # None = unresolved
    qty: int
    unit_price: float
    line_total: float
    match_confidence: str   # "exact", "fuzzy", "unresolved"
    match_notes: Optional[str]


@dataclass
class PipelineResult:
    project_name: str
    resolved: list[ResolvedItem]
    unresolved_codes: list[str]   # codes that had no catalog match
    subtotal: float
    source_drawings: list[str]
    catalog_file: str
    extracted_at: str   # ISO datetime
