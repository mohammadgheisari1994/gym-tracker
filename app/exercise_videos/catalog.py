"""Seed mapping of common exercises to a Jeff Nippard technique video.

These ids were taken from public YouTube search results for his channel and
should be spot-checked before being relied on; extend the list freely. Anything
not matched here is handled by the per-exercise "paste a URL" form and the
"search his channel" link on the exercise page. Videos are only ever embedded
through YouTube's official player, never downloaded.
"""

import re
from dataclasses import dataclass

_EQUIPMENT_WORDS = {
    "barbell",
    "dumbbell",
    "db",
    "machine",
    "cable",
    "smith",
    "bodyweight",
    "the",
}


@dataclass(frozen=True)
class SeededVideo:
    youtube_id: str
    title: str


SEED: dict[str, SeededVideo] = {
    "squat": SeededVideo("bEv6CCg2BC8", "How To Get A Huge Squat With Perfect Technique"),
    "back squat": SeededVideo("bEv6CCg2BC8", "How To Get A Huge Squat With Perfect Technique"),
    "bench press": SeededVideo(
        "vcBig73ojpE", "How To Get A Huge Bench Press With Perfect Technique"
    ),
    "deadlift": SeededVideo("ZaTM37cfiDs", "How To Deadlift With Perfect Technique (Step By Step)"),
    "conventional deadlift": SeededVideo(
        "ZaTM37cfiDs", "How To Deadlift With Perfect Technique (Step By Step)"
    ),
    "overhead press": SeededVideo(
        "_RlRDWO2jfg", "Build Bigger Shoulders With Perfect Technique (Overhead Press)"
    ),
}


def _normalise(name: str) -> str:
    words = re.findall(r"[a-z0-9]+", name.lower())
    kept = [w for w in words if w not in _EQUIPMENT_WORDS]
    return " ".join(kept or words)


def match_video(name: str) -> SeededVideo | None:
    key = _normalise(name)
    if key in SEED:
        return SEED[key]
    for seed_key, video in SEED.items():
        if seed_key in key:
            return video
    return None
