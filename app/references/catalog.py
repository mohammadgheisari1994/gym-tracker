"""The reference catalogue.

Every DOI below was verified against the Crossref API before being committed.
Scientific works are *cited* here, never reproduced: the full text remains with
the respective publishers. Instructional videos are embedded through YouTube's
official player and are not downloaded or re-hosted.
"""

from dataclasses import dataclass
from typing import Literal

ReferenceKind = Literal["position_stand", "paper", "formula", "media"]


@dataclass(frozen=True, slots=True)
class Reference:
    slug: str
    kind: ReferenceKind
    authors: str
    year: int
    title: str
    source: str
    doi: str | None = None
    url: str = ""
    access: str = ""

    @property
    def link(self) -> str:
        """The canonical, resolvable link for this reference."""
        return f"https://doi.org/{self.doi}" if self.doi else self.url


def format_citation(ref: Reference) -> str:
    """Render a compact, APA-flavoured citation string."""
    return f"{ref.authors} ({ref.year}). {ref.title}. {ref.source}. {ref.link}"


CATALOG: tuple[Reference, ...] = (
    Reference(
        slug="acsm-2009-progression",
        kind="position_stand",
        authors="American College of Sports Medicine (Ratamess, N. A., et al.)",
        year=2009,
        title="Progression models in resistance training for healthy adults",
        source="Medicine & Science in Sports & Exercise, 41(3), 687–708",
        doi="10.1249/MSS.0b013e3181915670",
        access="Publisher paywall; official ACSM position stand.",
    ),
    Reference(
        slug="schoenfeld-2010-hypertrophy-mechanisms",
        kind="paper",
        authors="Schoenfeld, B. J.",
        year=2010,
        title=("The mechanisms of muscle hypertrophy and their application to resistance training"),
        source="Journal of Strength and Conditioning Research, 24(10), 2857–2872",
        doi="10.1519/JSC.0b013e3181e840f3",
        access="Publisher paywall; abstract freely available.",
    ),
    Reference(
        slug="schoenfeld-2017-volume",
        kind="paper",
        authors="Schoenfeld, B. J., Ogborn, D., & Krieger, J. W.",
        year=2017,
        title=(
            "Dose-response relationship between weekly resistance training "
            "volume and increases in muscle mass: A systematic review and "
            "meta-analysis"
        ),
        source="Journal of Sports Sciences, 35(11), 1073–1082",
        doi="10.1080/02640414.2016.1210197",
        access="Publisher paywall; abstract freely available.",
    ),
    Reference(
        slug="schoenfeld-2016-frequency",
        kind="paper",
        authors="Schoenfeld, B. J., Ogborn, D., & Krieger, J. W.",
        year=2016,
        title=(
            "Effects of resistance training frequency on measures of muscle "
            "hypertrophy: A systematic review and meta-analysis"
        ),
        source="Sports Medicine, 46(11), 1689–1697",
        doi="10.1007/s40279-016-0543-8",
        access="Publisher paywall; abstract freely available.",
    ),
    Reference(
        slug="grgic-2018-rest-intervals",
        kind="paper",
        authors="Grgic, J., Schoenfeld, B. J., Skrepnik, M., Davies, T. B., & Mikulic, P.",
        year=2018,
        title=(
            "Effects of rest interval duration in resistance training on "
            "measures of muscular strength: A systematic review"
        ),
        source="Sports Medicine, 48(1), 137–151",
        doi="10.1007/s40279-017-0788-x",
        access="Publisher paywall; abstract freely available.",
    ),
    Reference(
        slug="zourdos-2016-rir-rpe",
        kind="paper",
        authors="Zourdos, M. C., Klemp, A., Dolan, C., et al.",
        year=2016,
        title=(
            "Novel resistance training-specific rating of perceived exertion "
            "scale measuring repetitions in reserve"
        ),
        source="Journal of Strength and Conditioning Research, 30(1), 267–275",
        doi="10.1519/JSC.0000000000001049",
        access="Publisher paywall; abstract freely available.",
    ),
    Reference(
        slug="androulakis-korakakis-2020-minimum-dose",
        kind="paper",
        authors="Androulakis-Korakakis, P., Fisher, J. P., & Steele, J.",
        year=2020,
        title=(
            "The minimum effective training dose required to increase 1RM "
            "strength in resistance-trained men: A systematic review and "
            "meta-analysis"
        ),
        source="Sports Medicine, 50(4), 751–765",
        doi="10.1007/s40279-019-01236-0",
        access="Publisher paywall; abstract freely available.",
    ),
    Reference(
        slug="brzycki-1993-1rm",
        kind="formula",
        authors="Brzycki, M.",
        year=1993,
        title="Strength testing—predicting a one-rep max from reps-to-fatigue",
        source="Journal of Physical Education, Recreation & Dance, 64(1), 88–90",
        doi="10.1080/07303084.1993.10606684",
        access="Publisher paywall; source of the Brzycki 1RM equation.",
    ),
    Reference(
        slug="lesuer-1997-1rm-accuracy",
        kind="formula",
        authors=(
            "LeSuer, D. A., McCormick, J. H., Mayhew, J. L., Wasserstein, R. L., & Arnold, M. D."
        ),
        year=1997,
        title=(
            "The accuracy of prediction equations for estimating 1-RM "
            "performance in the bench press, squat, and deadlift"
        ),
        source="Journal of Strength and Conditioning Research, 11(4), 211–213",
        url="https://www.semanticscholar.org/paper/e2c1cba24a3a4fb342f29dacf21b73226b51ad22",
        access="Publisher paywall; validation of common 1RM equations.",
    ),
    Reference(
        slug="epley-1985-poundage-chart",
        kind="formula",
        authors="Epley, B.",
        year=1985,
        title="Poundage chart",
        source="Boyd Epley Workout. Lincoln, NE: Body Enterprises",
        url="https://en.wikipedia.org/wiki/One-repetition_maximum#Epley_formula",
        access=(
            "Primary source is a printed chart; the Epley equation gym-tracker "
            "uses for estimated 1RM is documented in LeSuer et al. (1997) and "
            "standard NSCA texts."
        ),
    ),
    Reference(
        slug="jeff-nippard-youtube",
        kind="media",
        authors="Jeff Nippard",
        year=2026,
        title="Jeff Nippard — evidence-based lifting technique videos",
        source="YouTube",
        url="https://www.youtube.com/@JeffNippard",
        access=(
            "Per-exercise instructional videos are embedded through YouTube's "
            "official player and remain © their creator. gym-tracker does not "
            "download, store, or redistribute video files."
        ),
    ),
)

_BY_SLUG: dict[str, Reference] = {ref.slug: ref for ref in CATALOG}


def by_slug(slug: str) -> Reference:
    """Return one reference, raising ``KeyError`` for an unknown slug."""
    return _BY_SLUG[slug]


def get_many(slugs: list[str]) -> list[Reference]:
    """Resolve a list of slugs, preserving order.

    Raises ``KeyError`` if any slug is unknown so that a guide can never point at
    a reference that does not exist.
    """
    return [by_slug(slug) for slug in slugs]
