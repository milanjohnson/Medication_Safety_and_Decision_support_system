# SOURCE: NOT IN PAPERS. Stage names are the team's six-stage design as given in the task prompt
# (only stages 2, 4, 5 and 6 are named there). A stage of None means "not confirmed by the user":
# it is shown as "to be confirmed", never guessed.
"""Modules that are not built. They appear as "coming soon" and carry no data."""
from __future__ import annotations

from dataclasses import dataclass

STAGE_NAMES = {
    2: "Information extraction and retrieval of medicine knowledge",
    4: "AI risk and safety engine",
    5: "Recommendation engine",
    6: "Explanation generator",
}


@dataclass(frozen=True)
class ComingSoonModule:
    id: str
    label: str
    stage: int | None


COMING_SOON: tuple[ComingSoonModule, ...] = (
    ComingSoonModule("allergy_check", "Allergy Check", None),
    ComingSoonModule("contraindication_check", "Contraindication Check", None),
    ComingSoonModule("duplicate_therapy_check", "Duplicate Therapy Check", None),
    ComingSoonModule("disease_precautions", "Disease Precautions", None),
    ComingSoonModule("full_patient_profile", "Full Patient Profile", None),
    ComingSoonModule("deep_learning_encoder", "Deep-learning encoder", 2),
    ComingSoonModule("focal_loss_model", "Focal Loss interaction model", 4),
)
