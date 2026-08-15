"""
trip_models.py

Core structured data models for VOYA.

This file defines the shared data language used by the system.
It does not contain AI calls, decision scoring, API calls, or UI logic.
"""

from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any, Optional


class ActivityPriority(str, Enum):
    MUST_DO = "must_do"
    IMPORTANT = "important"
    FLEXIBLE = "flexible"
    OPTIONAL = "optional"


class ActivityStatus(str, Enum):
    PLANNED = "planned"
    CURRENT = "current"
    COMPLETED = "completed"
    SKIPPED = "skipped"
    CANCELLED = "cancelled"


class DependencyType(str, Enum):
    AFTER = "after"
    BEFORE = "before"
    SAME_DAY = "same_day"
    SAME_AREA = "same_area"


@dataclass
class ActivityDependency:
    """
    A relationship between one activity and another.

    Example:
    - activity 5 must happen after activity 2
    - activity 7 should stay in the same area as activity 6
    """

    other_activity_id: int
    dependency_type: DependencyType
    reason: str = ""

    def to_dict(self) -> dict:
        return {
            "other_activity_id": self.other_activity_id,
            "dependency_type": self.dependency_type.value,
            "reason": self.reason,
        }


@dataclass
class Activity:
    # --------------------------------------------------
    # Basic identity
    # --------------------------------------------------
    id: int
    name: str
    category: str

    # --------------------------------------------------
    # Location
    # --------------------------------------------------
    lat: Optional[float] = None
    lon: Optional[float] = None
    area_group: Optional[str] = None

    # --------------------------------------------------
    # Schedule
    # --------------------------------------------------
    day: Optional[int] = None
    start_time: Optional[str] = None
    duration_minutes: Optional[int] = None

    # --------------------------------------------------
    # Existing VOYA / POI information
    # --------------------------------------------------
    place_type: Optional[str] = None
    source: str = "unknown"
    source_id: Optional[str] = None

    # --------------------------------------------------
    # Importance / user intent
    # --------------------------------------------------
    importance_score: int = 5
    priority: ActivityPriority = ActivityPriority.FLEXIBLE
    must_do: bool = False
    reason: str = ""
    important_for: list[str] = field(default_factory=list)

    # --------------------------------------------------
    # Booking / movement constraints
    # --------------------------------------------------
    booked: bool = False
    paid: bool = False

    movable: bool = True
    movable_to_other_day: bool = True
    removable: bool = True

    fixed_time: bool = False
    earliest_start: Optional[str] = None
    latest_start: Optional[str] = None

    locked: bool = False

    # --------------------------------------------------
    # Live trip state
    # --------------------------------------------------
    status: ActivityStatus = ActivityStatus.PLANNED

    # --------------------------------------------------
    # Relationships to other activities
    # --------------------------------------------------
    dependencies: list[ActivityDependency] = field(
        default_factory=list
    )

    def __post_init__(self):
        if not 1 <= self.importance_score <= 10:
            raise ValueError(
                "importance_score must be between 1 and 10."
            )

        if self.duration_minutes is not None:
            if self.duration_minutes <= 0:
                raise ValueError(
                    "duration_minutes must be greater than 0."
                )

        if self.must_do:
            self.priority = ActivityPriority.MUST_DO

    def to_dict(self) -> dict:
        data = asdict(self)

        data["priority"] = self.priority.value
        data["status"] = self.status.value

        data["dependencies"] = [
            dependency.to_dict()
            for dependency in self.dependencies
        ]

        return data


@dataclass
class TripIntent:
    """
    What the user wants from the current trip.

    Trip-specific intent should normally override
    long-term preferences when they conflict.
    """

    travelers: int = 1
    budget: str = "בינוני"
    pace: str = "מאוזן"
    interests: list[str] = field(default_factory=list)
    notes: str = ""

    must_do_names: list[str] = field(default_factory=list)
    avoid: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class TripState:
    """
    The current live state of the trip.
    """

    current_day: int = 1
    current_time: Optional[str] = None

    current_lat: Optional[float] = None
    current_lon: Optional[float] = None

    current_activity_id: Optional[int] = None

    completed_activity_ids: list[int] = field(default_factory=list)
    skipped_activity_ids: list[int] = field(default_factory=list)

    remaining_budget: Optional[float] = None
    free_time_minutes: int = 0

    activities: list[Activity] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "current_day": self.current_day,
            "current_time": self.current_time,
            "current_lat": self.current_lat,
            "current_lon": self.current_lon,
            "current_activity_id": self.current_activity_id,
            "completed_activity_ids": self.completed_activity_ids,
            "skipped_activity_ids": self.skipped_activity_ids,
            "remaining_budget": self.remaining_budget,
            "free_time_minutes": self.free_time_minutes,
            "activities": [
                activity.to_dict()
                for activity in self.activities
            ],
        }


@dataclass
class LiveFact:
    """
    A fact coming from an external source.

    Examples:
    - weather
    - opening status
    - travel time
    - closure
    - congestion

    OpenAI should reason about supplied facts rather than invent them.
    """

    fact_type: str
    value: Any
    source: str

    confidence: float = 1.0
    observed_at: Optional[str] = None
    valid_until: Optional[str] = None

    def __post_init__(self):
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError(
                "confidence must be between 0.0 and 1.0."
            )

    def to_dict(self) -> dict:
        return asdict(self)
