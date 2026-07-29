from enum import StrEnum


class MatchAnalysisStatus(StrEnum):
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"


class MatchDepth(StrEnum):
    SCREEN = "screen"
    FULL = "full"
