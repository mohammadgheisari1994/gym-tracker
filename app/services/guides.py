"""LLM-generated exercise execution guides, cached permanently per exercise.

The user never types a prompt: the system and user messages are built here from
the exercise's own fields.
"""

import logging

from sqlalchemy.orm import Session

from app.llm import LLMProvider, get_provider
from app.models import Exercise, ExerciseGuide

logger = logging.getLogger(__name__)

# Works every generated guide links to as "further reading". The guide text is
# original; these are not its source.
GUIDE_SOURCE_SLUGS: tuple[str, ...] = (
    "acsm-2009-progression",
    "schoenfeld-2010-hypertrophy-mechanisms",
    "jeff-nippard-youtube",
)

_SYSTEM_PROMPT = (
    "You are a strength and conditioning coach writing a short, practical "
    "exercise execution guide for a training-log app. Output plain text only. "
    "Structure it as: one line starting 'Setup:'; then 3 to 6 numbered "
    "execution steps; then 2 to 4 lines starting 'Range of motion:' covering the "
    "key ROM cues. Be specific, safe, and readable by a beginner. Do NOT name "
    "any person, brand, book, company, website, or video. Do NOT copy wording "
    "from any source — write it entirely in your own words. Keep the whole "
    "guide between 120 and 220 words."
)


def _user_prompt(exercise: Exercise) -> str:
    return f"Exercise name: {exercise.name}\nPrimary muscle group: {exercise.muscle_group.value}"


def generate_guide(
    session: Session,
    exercise: Exercise,
    *,
    provider: LLMProvider | None = None,
) -> ExerciseGuide:
    """Generate (or regenerate) and store the guide. Raises on provider errors."""
    provider = provider or get_provider()
    result = provider.complete(system=_SYSTEM_PROMPT, prompt=_user_prompt(exercise), max_tokens=600)

    guide = exercise.guide or ExerciseGuide(exercise_id=exercise.id)
    guide.body = result.text
    guide.source_slugs = list(GUIDE_SOURCE_SLUGS)
    guide.provider = result.provider
    guide.model = result.model
    session.add(guide)
    exercise.guide = guide
    return guide


def generate_guide_in_background(exercise_id: int, provider: LLMProvider) -> None:
    """Fire-and-forget generation used right after an exercise is created."""
    if not provider.available:
        return

    from app.database import SessionLocal

    with SessionLocal() as session:
        exercise = session.get(Exercise, exercise_id)
        if exercise is None or exercise.guide is not None:
            return
        try:
            generate_guide(session, exercise, provider=provider)
            session.commit()
        except Exception:
            session.rollback()
            logger.exception("Failed to generate guide for exercise %s", exercise_id)
