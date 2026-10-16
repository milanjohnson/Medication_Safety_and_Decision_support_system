# SOURCE: NOT IN PAPERS. Component readiness comes only from what exists on disk. A component
# is "ready" when its files are present; nothing is reported ready on trust.
"""GET /api/status logic."""
from __future__ import annotations

import json
from pathlib import Path

from medsafe import ddi2013

from ..config import Settings
from ..modules import COMING_SOON, STAGE_NAMES
from ..schemas import ComponentStatus, ModuleStatus, StatusResponse
from . import datasets

INDEX_MANIFEST = "index/manifest.json"            # written by the Phase 3 index build
DDI_MODEL_FILES = ("ddi_baseline/model.joblib", "ddi_baseline/metrics.json")  # Phase 4 training


def _read_json(path: Path) -> dict | None:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def _ddi_data(s: Settings) -> ComponentStatus:
    base = dict(id="ddi_data", label="DDI Extraction 2013 corpus")
    if not datasets.ddi_has_files(s):
        return ComponentStatus(status="not_ready", **base,
                               reason=f"No .xml files found under {datasets.ddi_root(s)}.",
                               fix="Put the DDICorpus folder in data/ddi2013.")
    files = ddi2013.classify_files(datasets.ddi_root(s))
    detail = {f"xml_{k}": len(v) for k, v in files.items()}
    return ComponentStatus(status="ready", **base, detail=detail)


def _tac_data(s: Settings) -> ComponentStatus:
    base = dict(id="tac_data", label="TAC 2017 labels")
    folder = s.data_dir / datasets.TAC_DIRNAME
    n = sum(1 for _ in folder.rglob("*.xml")) if folder.is_dir() else 0
    if n == 0:
        return ComponentStatus(status="not_ready", **base,
                               reason=f"No .xml files found under {folder}.",
                               fix="Put train_xml, gold_xml and unannotated_xml in data/tac2017.")
    return ComponentStatus(status="ready", **base, detail={"xml_files": n})


def _dailymed_data(s: Settings) -> ComponentStatus:
    base = dict(id="dailymed_data", label="DailyMed Rx label zips")
    zips = datasets.dailymed_zips(s)
    if not zips:
        return ComponentStatus(
            status="not_ready", **base,
            reason=f"No .zip files found in {s.data_dir / datasets.DAILYMED_DIRNAME}.",
            fix="Put dm_spl_release_human_rx_part*.zip in data/dailymed_rx.")
    return ComponentStatus(status="ready", **base, detail={
        "zip_files": len(zips), "total_bytes": sum(z.stat().st_size for z in zips),
        "files": ", ".join(z.name for z in zips)})


def _index(s: Settings) -> ComponentStatus:
    base = dict(id="index", label="Retrieval index")
    manifest = _read_json(s.artifacts_dir / INDEX_MANIFEST)
    if manifest is None:
        return ComponentStatus(
            status="not_ready", **base,
            reason=f"No index manifest at {s.artifacts_dir / INDEX_MANIFEST}.",
            fix="Needs the Phase 3 index build, which is not implemented yet, and DailyMed labels.")
    return ComponentStatus(status="ready", **base, detail={
        k: v for k, v in manifest.items() if isinstance(v, (str, int, float))})


def _encoder(s: Settings) -> ComponentStatus:
    base = dict(id="encoder", label=f"Encoder (configured: {s.encoder_name})")
    manifest = _read_json(s.artifacts_dir / INDEX_MANIFEST)
    if manifest is None or "encoder" not in manifest:
        return ComponentStatus(
            status="not_ready", **base,
            reason="No encoder is loaded: the encoder is recorded when an index is built, "
                   "and there is no index.",
            fix="Needs the Phase 3 encoder and index build, which are not implemented yet.")
    return ComponentStatus(status="ready", **base, detail={"encoder": str(manifest["encoder"])})


def _ddi_model(s: Settings) -> ComponentStatus:
    base = dict(id="ddi_model", label=f"DDI classifier (configured: {s.classifier_name})")
    missing = [f for f in DDI_MODEL_FILES if not (s.artifacts_dir / f).is_file()]
    if missing:
        return ComponentStatus(
            status="not_ready", **base,
            reason=f"Missing in {s.artifacts_dir}: {', '.join(missing)}.",
            fix="Needs the Phase 4 training script, which is not implemented yet.")
    return ComponentStatus(status="ready", **base, detail={"classifier": s.classifier_name})


def get_status(s: Settings) -> StatusResponse:
    return StatusResponse(
        components=[_ddi_data(s), _tac_data(s), _dailymed_data(s), _encoder(s), _index(s),
                    _ddi_model(s)],
        modules=[ModuleStatus(id=m.id, label=m.label, stage=m.stage,
                              stage_name=STAGE_NAMES.get(m.stage) if m.stage else None)
                 for m in COMING_SOON],
        active_encoder=s.encoder_name, active_classifier=s.classifier_name,
        data_dir=str(s.data_dir))
