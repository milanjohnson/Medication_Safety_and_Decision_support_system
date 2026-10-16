# SOURCE: NOT IN PAPERS. Typed request/response models for the API.
"""Every endpoint returns one of these. A component whose data is missing returns
status="not_ready" with a reason and a fix, never placeholder numbers."""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

DDILabel = Literal["effect", "mechanism", "advise", "int", "false"]


class ApiModel(BaseModel):
    # Fields with defaults are always present in a response, so the generated TypeScript types
    # must not mark them optional.
    model_config = ConfigDict(json_schema_serialization_defaults_required=True)


class Readiness(ApiModel):
    status: Literal["ready", "not_ready"]
    reason: str | None = None
    fix: str | None = None


class Health(ApiModel):
    status: Literal["ok"] = "ok"


# ---- /api/status -------------------------------------------------------------------------
class ComponentStatus(Readiness):
    id: str
    label: str
    detail: dict[str, str | int | float] = Field(default_factory=dict)


class ModuleStatus(ApiModel):
    id: str
    label: str
    status: Literal["coming_soon"] = "coming_soon"
    stages: list[int]
    stage_names: list[str]
    owner: str = "to be confirmed"


class StageInfo(ApiModel):
    number: int
    name: str
    in_scope: bool  # covered by this app (stages 2, 4, 5, 6 per the project brief)


class StatusResponse(ApiModel):
    components: list[ComponentStatus]
    modules: list[ModuleStatus]
    stages: list[StageInfo]
    active_encoder: str
    active_classifier: str
    data_dir: str


# ---- DDI 2013 -----------------------------------------------------------------------------
class DDISplitStats(ApiModel):
    split: Literal["train", "dev", "test"]
    instances: int
    class_counts: dict[str, int]
    imbalance_false_to_class: dict[str, float | None]
    by_source: dict[str, int]


class DDIParserStats(ApiModel):
    """Counts straight from the parser, before the dev split is carved out of train."""
    split: Literal["train_all", "test"]
    counts: dict[str, int]


class DDIStatsResponse(Readiness):
    labels: list[str] = Field(default_factory=list)
    files_by_split: dict[str, int] = Field(default_factory=dict)
    splits: list[DDISplitStats] = Field(default_factory=list)
    parser: list[DDIParserStats] = Field(default_factory=list)
    dev_frac: float | None = None
    seed: int | None = None


class DDIExample(ApiModel):
    split: Literal["train", "dev", "test"]
    label: DDILabel
    source: str
    doc_id: str
    sent_id: str
    pair_id: str
    e1_text: str
    e2_text: str
    text: str
    marked_text: str


class DDIExamplesResponse(Readiness):
    total_matching: int = 0
    examples: list[DDIExample] = Field(default_factory=list)


# ---- DailyMed / TAC ----------------------------------------------------------------------
class ZipFileInfo(ApiModel):
    name: str
    size_bytes: int


class DailyMedStatsResponse(Readiness):
    zip_files: list[ZipFileInfo] = Field(default_factory=list)
    parts_loaded: list[str] = Field(default_factory=list)
    # is_sample/scope come from the stats file itself: a capped run must never read as a full count
    is_sample: bool | None = None
    scope: str | None = None
    sample_limit_per_part: int | None = None
    zip_entries: dict[str, int] = Field(default_factory=dict)
    labels_parsed: int | None = None
    parse_failures: int | None = None
    labels_per_section: dict[str, int] = Field(default_factory=dict)
    chunks: int | None = None
    chunks_per_section: dict[str, int] = Field(default_factory=dict)
    chunk_size: int | None = None
    chunk_overlap: int | None = None
    distinct_ingredients: int | None = None
    distinct_active_moieties: int | None = None
    distinct_manufacturers: int | None = None
    labels_without_any_section: int | None = None
    ingredient_source: dict[str, int] = Field(default_factory=dict)
    peak_working_set_mb: float | None = None
    parse_stats: dict[str, int] = Field(default_factory=dict)
    elapsed_seconds: float | None = None
    generated_at: str | None = None


class TacStatsResponse(Readiness):
    labels_per_split: dict[str, int] = Field(default_factory=dict)
    section_names: dict[str, int] = Field(default_factory=dict)
    mention_types: dict[str, int] = Field(default_factory=dict)
    relation_types: dict[str, int] = Field(default_factory=dict)
    mentions: int | None = None
    relations: int | None = None
    reactions: int | None = None
    labels_without_text: int | None = None
    parse_failures: int | None = None


# ---- /api/trace --------------------------------------------------------------------------
TraceCategory = Literal["from_papers", "from_baseline_review", "not_in_papers", "unclassified"]
TraceStatusKind = Literal["untested", "ran", "verified", "unknown"]


class TraceRow(ApiModel):
    component: str
    file: str
    source: str
    note: str
    status: str | None = None
    category: TraceCategory
    status_kind: TraceStatusKind


class TraceResponse(Readiness):
    rows: list[TraceRow] = Field(default_factory=list)
    counts_by_category: dict[str, int] = Field(default_factory=dict)
    counts_by_status: dict[str, int] = Field(default_factory=dict)
    malformed_rows: list[str] = Field(default_factory=list)
    preamble: list[str] = Field(default_factory=list)
