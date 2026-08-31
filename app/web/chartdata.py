"""Turn analytics dataclasses into plain JSON-serialisable chart payloads."""

from collections.abc import Callable

from app.services.analytics import ExercisePoint, OverallStats


def _num(value) -> float | None:
    return float(value) if value is not None else None


def overall_chart_data(stats: OverallStats, translate: Callable[[str], str]) -> dict:
    return {
        "weeklyVolume": {
            "labels": [label for label, _ in stats.weekly_volume],
            "values": [_num(value) for _, value in stats.weekly_volume],
        },
        "weeklyFrequency": {
            "labels": [label for label, _ in stats.weekly_frequency],
            "values": [count for _, count in stats.weekly_frequency],
        },
        "muscleDistribution": {
            "labels": [
                translate(f"exercises.muscle.{mv.muscle_group.value}")
                for mv in stats.muscle_distribution
            ],
            "values": [_num(mv.volume) for mv in stats.muscle_distribution],
        },
    }


def exercise_chart_data(points: list[ExercisePoint]) -> dict:
    return {
        "labels": [point.on.isoformat() for point in points],
        "topWeight": [_num(point.top_weight) for point in points],
        "estimatedOneRepMax": [_num(point.best_e1rm) for point in points],
        "volume": [_num(point.volume) for point in points],
        "reps": [point.reps for point in points],
    }
