from dataclasses import dataclass
from datetime import date


@dataclass
class Subject:
    name: str
    exam_date: date
    difficulty: int


@dataclass
class StudyBlock:
    date: date
    subject: str
    hours: float
    completed: bool = False
