from datetime import date
from models import Subject


def validate_difficulty(difficulty: int) -> int:
    """Validate that difficulty is an integer between 1 and 5 inclusive."""
    if isinstance(difficulty, bool) or not isinstance(difficulty, (int, float)):
        raise ValueError("Difficulty must be an integer between 1 and 5.")
    if difficulty != int(difficulty) or difficulty < 1 or difficulty > 5:
        raise ValueError("Difficulty must be an integer between 1 and 5.")
    return int(difficulty)


def validate_available_hours(hours: float) -> float:
    """Validate that available hours per day is a positive number."""
    if isinstance(hours, bool) or not isinstance(hours, (int, float)):
        raise ValueError("Available study hours must be a positive number.")
    if hours <= 0:
        raise ValueError("Available study hours must be a positive number.")
    return float(hours)


def validate_subject(subject: Subject) -> None:
    """Validate all fields of a Subject instance."""
    if not isinstance(subject, Subject):
        raise ValueError("Expected a Subject instance.")
    if not isinstance(subject.name, str) or not subject.name.strip():
        raise ValueError("Subject name cannot be empty.")
    if not isinstance(subject.exam_date, date):
        raise ValueError("Exam date must be a valid date object.")
    validate_difficulty(subject.difficulty)


def days_until_exam(exam_date: date, current_date: date) -> int:
    """Return the number of days from current_date to exam_date."""
    return (exam_date - current_date).days
