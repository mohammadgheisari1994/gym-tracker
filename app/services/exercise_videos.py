"""Per-exercise instructional videos.

Videos are only ever embedded through YouTube's official player. Nothing is
downloaded. A small curated seed auto-attaches for common lifts; anything else
is set by the user pasting a link.
"""

import re
from urllib.parse import quote

from sqlalchemy.orm import Session

from app.exercise_videos import match_video
from app.models import Exercise, ExerciseVideo
from app.services.errors import ServiceError

_YT_ID = r"[A-Za-z0-9_-]{11}"
_PATTERNS = [
    re.compile(rf"[?&]v=({_YT_ID})"),
    re.compile(rf"youtu\.be/({_YT_ID})"),
    re.compile(rf"/embed/({_YT_ID})"),
    re.compile(rf"/shorts/({_YT_ID})"),
    re.compile(rf"/live/({_YT_ID})"),
    re.compile(rf"^({_YT_ID})$"),
]


class InvalidVideoUrl(ServiceError):
    pass


def extract_youtube_id(value: str) -> str | None:
    value = value.strip()
    for pattern in _PATTERNS:
        match = pattern.search(value)
        if match:
            return match.group(1)
    return None


def embed_url(youtube_id: str) -> str:
    return f"https://www.youtube-nocookie.com/embed/{youtube_id}"


def watch_url(youtube_id: str) -> str:
    return f"https://www.youtube.com/watch?v={youtube_id}"


def nippard_search_url(exercise_name: str) -> str:
    return f"https://www.youtube.com/@JeffNippard/search?query={quote(exercise_name)}"


def attach_seed_video(session: Session, exercise: Exercise) -> ExerciseVideo | None:
    """Attach the curated video for this exercise if its name matches one."""
    if exercise.video is not None:
        return exercise.video
    seeded = match_video(exercise.name)
    if seeded is None:
        return None
    video = ExerciseVideo(
        exercise_id=exercise.id,
        youtube_id=seeded.youtube_id,
        title=seeded.title,
        source="seed",
    )
    session.add(video)
    exercise.video = video
    return video


def set_manual_video(session: Session, exercise: Exercise, raw: str) -> ExerciseVideo:
    youtube_id = extract_youtube_id(raw)
    if youtube_id is None:
        raise InvalidVideoUrl

    video = exercise.video or ExerciseVideo(exercise_id=exercise.id)
    video.youtube_id = youtube_id
    video.title = None
    video.source = "manual"
    session.add(video)
    exercise.video = video
    return video


def clear_video(session: Session, exercise: Exercise) -> None:
    if exercise.video is not None:
        session.delete(exercise.video)
        exercise.video = None
