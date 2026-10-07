from datetime import date, timedelta
from models import Subject, StudyBlock
from utils import (
    validate_available_hours,
    validate_difficulty,
    validate_subject,
    days_until_exam,
)


def calculate_priority(subject: Subject, current_date: date) -> float:
    """
    Calculate rule-based priority score for a subject on a given date.
    Priority = Difficulty * Urgency
    Urgency = 1.0 / (days_remaining + 1)
    """
    days = days_until_exam(subject.exam_date, current_date)
    if days < 0:
        return 0.0

    urgency = 1.0 / (days + 1)
    return subject.difficulty * urgency


def allocate_daily_hours(
    active_subjects: list[Subject],
    available_hours: float,
    current_date: date,
) -> list[StudyBlock]:
    """
    Allocate available study hours among active subjects for current_date
    using a deterministic greedy 0.5-hour chunk algorithm.
    Guarantees sum(hours) <= available_hours.
    """
    if not active_subjects or available_hours <= 0:
        return []

    # Calculate priority for each active subject
    subject_priorities = []
    for subj in active_subjects:
        p = calculate_priority(subj, current_date)
        if p > 0:
            subject_priorities.append((subj, p))

    if not subject_priorities:
        return []

    # Determine step size (0.5h standard or available_hours if < 0.5h)
    step_size = 0.5 if available_hours >= 0.5 else available_hours
    total_chunks = int(available_hours / step_size)
    if total_chunks <= 0:
        return []

    total_priority = sum(p for _, p in subject_priorities)
    if total_priority <= 0:
        return []

    # Calculate continuous quotas and base chunk allocations
    quotas = []
    base_chunks_sum = 0

    for subj, p in subject_priorities:
        quota = total_chunks * (p / total_priority)
        base = int(quota)
        rem = quota - base
        base_chunks_sum += base
        quotas.append({
            "subject": subj,
            "priority": p,
            "quota": quota,
            "base": base,
            "rem": rem,
            "extra": 0,
        })

    remaining_chunks = total_chunks - base_chunks_sum

    # Distribute remaining chunks deterministically:
    # Sort by remainder desc, priority desc, exam_date asc, name asc
    if remaining_chunks > 0:
        sorted_quotas = sorted(
            quotas,
            key=lambda x: (
                -x["rem"],
                -x["priority"],
                x["subject"].exam_date,
                x["subject"].name,
            ),
        )
        for i in range(min(remaining_chunks, len(sorted_quotas))):
            sorted_quotas[i]["extra"] += 1

    # Build StudyBlock results for subjects receiving > 0 hours
    blocks = []
    # Sort output blocks deterministically by priority desc, exam_date asc, name asc
    quotas.sort(
        key=lambda x: (
            -x["priority"],
            x["subject"].exam_date,
            x["subject"].name,
        )
    )

    for item in quotas:
        assigned_chunks = item["base"] + item["extra"]
        if assigned_chunks > 0:
            assigned_hours = round(assigned_chunks * step_size, 2)
            blocks.append(
                StudyBlock(
                    date=current_date,
                    subject=item["subject"].name,
                    hours=assigned_hours,
                    completed=False,
                )
            )

    return blocks


def generate_schedule(
    subjects: list[Subject],
    available_hours_per_day: float,
    start_date: date | None = None,
) -> list[StudyBlock]:
    """
    Generate a deterministic, day-by-day study timetable.

    API Contract:
        generate_schedule(subjects, available_hours_per_day, start_date=None)

    Args:
        subjects: List of Subject dataclasses.
        available_hours_per_day: Maximum hours available for study per day.
        start_date: Starting date for schedule (defaults to date.today()).

    Returns:
        List of StudyBlock dataclasses.
    """
    # 1. Input Validation
    validated_hours = validate_available_hours(available_hours_per_day)

    if not subjects:
        return []

    for subj in subjects:
        validate_subject(subj)

    if start_date is None:
        start_date = date.today()

    # 2. Filter subjects that have exam_date >= start_date
    valid_subjects = [s for s in subjects if s.exam_date >= start_date]
    if not valid_subjects:
        return []

    # 3. Determine schedule end date (latest exam date among valid subjects)
    max_exam_date = max(s.exam_date for s in valid_subjects)

    # 4. Generate day-by-day timetable
    full_schedule: list[StudyBlock] = []
    current_date = start_date

    while current_date <= max_exam_date:
        # Active subjects on current_date are those whose exam is today or in the future
        active_on_day = [s for s in valid_subjects if s.exam_date >= current_date]
        if not active_on_day:
            break

        day_blocks = allocate_daily_hours(active_on_day, validated_hours, current_date)
        full_schedule.extend(day_blocks)

        current_date += timedelta(days=1)

    return full_schedule
