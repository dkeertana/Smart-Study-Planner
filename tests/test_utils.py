from datetime import date, timedelta
import pytest

from models import Subject, StudyBlock
from scheduler import generate_schedule
from utils import (
    validate_subject_name,
    validate_difficulty,
    validate_available_hours,
    validate_exam_date,
    validate_subject,
    validate_subjects,
    days_until_exam,
    calculate_progress,
    reschedule_missed_tasks,
)


# =====================================================================
# 1. INPUT VALIDATION TESTS
# =====================================================================

def test_validate_subject_name():
    assert validate_subject_name("Mathematics") == "Mathematics"
    assert validate_subject_name("  Physics  ") == "Physics"

    with pytest.raises(ValueError, match="Subject name cannot be empty"):
        validate_subject_name("")

    with pytest.raises(ValueError, match="Subject name cannot be empty"):
        validate_subject_name("   ")

    with pytest.raises(ValueError, match="Subject name cannot be empty"):
        validate_subject_name(None)  # type: ignore


def test_validate_difficulty():
    assert validate_difficulty(1) == 1
    assert validate_difficulty(5) == 5
    assert validate_difficulty(3.0) == 3

    for invalid in [0, 6, -1, None, "three", True, False]:
        with pytest.raises(ValueError, match="Difficulty must be an integer between 1 and 5"):
            validate_difficulty(invalid)  # type: ignore


def test_validate_available_hours():
    assert validate_available_hours(4.0) == 4.0
    assert validate_available_hours(0.5) == 0.5
    assert validate_available_hours(12) == 12.0

    for invalid in [0, -1, -0.5, None, "four", True, False]:
        with pytest.raises(ValueError, match="Available study hours must be a positive number"):
            validate_available_hours(invalid)  # type: ignore


def test_validate_exam_date():
    today = date(2026, 10, 8)
    assert validate_exam_date(date(2026, 10, 10), today=today) == date(2026, 10, 10)
    assert validate_exam_date("2026-10-10", today=today) == date(2026, 10, 10)

    # Past date
    with pytest.raises(ValueError, match="Exam date cannot be in the past"):
        validate_exam_date(date(2026, 10, 5), today=today, check_past=True)

    # Invalid format string
    with pytest.raises(ValueError, match="Invalid exam date format"):
        validate_exam_date("invalid-date", today=today)


def test_duplicate_subject_names():
    today = date(2026, 10, 8)
    s1 = Subject("Mathematics", today + timedelta(days=5), 5)
    s2 = Subject("  mathematics  ", today + timedelta(days=8), 4)

    with pytest.raises(ValueError, match="Duplicate subject name found"):
        validate_subjects([s1, s2], today=today)


# =====================================================================
# 2. DATE UTILITY TESTS
# =====================================================================

def test_days_until_exam():
    ref_today = date(2026, 10, 8)

    assert days_until_exam(ref_today, today=ref_today) == 0
    assert days_until_exam(ref_today + timedelta(days=1), today=ref_today) == 1
    assert days_until_exam(ref_today + timedelta(days=5), today=ref_today) == 5
    assert days_until_exam(ref_today - timedelta(days=2), today=ref_today) == -2


# =====================================================================
# 3. PROGRESS CALCULATION TESTS
# =====================================================================

def test_calculate_progress_empty():
    res = calculate_progress([])
    assert res == {
        "total_hours": 0.0,
        "completed_hours": 0.0,
        "remaining_hours": 0.0,
        "progress_percentage": 0.0,
    }


def test_calculate_progress_no_completed():
    today = date(2026, 10, 8)
    blocks = [
        StudyBlock(today, "Math", 4.0, completed=False),
        StudyBlock(today, "Physics", 6.0, completed=False),
    ]
    res = calculate_progress(blocks)
    assert res["total_hours"] == 10.0
    assert res["completed_hours"] == 0.0
    assert res["remaining_hours"] == 10.0
    assert res["progress_percentage"] == 0.0


def test_calculate_progress_partially_completed():
    today = date(2026, 10, 8)
    blocks = [
        StudyBlock(today, "Math", 4.0, completed=True),
        StudyBlock(today, "Physics", 6.0, completed=False),
    ]
    res = calculate_progress(blocks)
    assert res["total_hours"] == 10.0
    assert res["completed_hours"] == 4.0
    assert res["remaining_hours"] == 6.0
    assert res["progress_percentage"] == 40.0


def test_calculate_progress_fully_completed():
    today = date(2026, 10, 8)
    blocks = [
        StudyBlock(today, "Math", 4.0, completed=True),
        StudyBlock(today, "Physics", 6.0, completed=True),
    ]
    res = calculate_progress(blocks)
    assert res["total_hours"] == 10.0
    assert res["completed_hours"] == 10.0
    assert res["remaining_hours"] == 0.0
    assert res["progress_percentage"] == 100.0


# =====================================================================
# 4. ADAPTIVE RESCHEDULING TESTS
# =====================================================================

def test_reschedule_missed_task():
    """Test 1: Missed task is redistributed into future available days."""
    today = date(2026, 10, 8)
    subjects = [
        Subject("Math", today + timedelta(days=5), 5),
        Subject("Physics", today + timedelta(days=5), 4),
    ]
    initial_blocks = [
        # Past missed block on yesterday
        StudyBlock(today - timedelta(days=1), "Math", 2.0, completed=False),
        # Scheduled today
        StudyBlock(today, "Physics", 2.0, completed=False),
    ]

    res = reschedule_missed_tasks(
        initial_blocks, available_hours_per_day=4.0, subjects=subjects, today=today
    )

    new_schedule = res["schedule"]
    assert res["unallocated_hours"] == 0.0
    assert res["rescheduled_hours"] == 2.0

    # Check that missed 2.0h Math was scheduled on or after today
    math_future_hours = sum(
        b.hours for b in new_schedule if b.subject == "Math" and b.date >= today
    )
    assert math_future_hours == 2.0


def test_reschedule_no_missed_tasks():
    """Test 2: No missed tasks returns unchanged schedule."""
    today = date(2026, 10, 8)
    initial_blocks = [
        StudyBlock(today - timedelta(days=1), "Math", 2.0, completed=True),
        StudyBlock(today, "Physics", 2.0, completed=False),
    ]

    res = reschedule_missed_tasks(initial_blocks, available_hours_per_day=4.0, today=today)
    assert res["schedule"] == initial_blocks
    assert res["unallocated_hours"] == 0.0


def test_reschedule_preserve_completed():
    """Test 3: Completed tasks are preserved on their original dates."""
    today = date(2026, 10, 8)
    completed_block = StudyBlock(today - timedelta(days=2), "Math", 2.0, completed=True)
    missed_block = StudyBlock(today - timedelta(days=1), "Physics", 2.0, completed=False)

    res = reschedule_missed_tasks(
        [completed_block, missed_block], available_hours_per_day=4.0, today=today
    )

    new_schedule = res["schedule"]
    assert completed_block in new_schedule


def test_reschedule_daily_capacity():
    """Test 4: Total daily hours after rescheduling never exceed available hours."""
    today = date(2026, 10, 8)
    subjects = [Subject("Math", today + timedelta(days=5), 5)]
    blocks = [
        StudyBlock(today - timedelta(days=1), "Math", 4.0, completed=False),
        StudyBlock(today, "Math", 3.0, completed=False),
    ]

    res = reschedule_missed_tasks(
        blocks, available_hours_per_day=4.0, subjects=subjects, today=today
    )

    by_date = {}
    for b in res["schedule"]:
        by_date[b.date] = by_date.get(b.date, 0.0) + b.hours

    for d, h in by_date.items():
        assert h <= 4.0 + 1e-6, f"Day {d} exceeded 4.0h capacity: {h}"


def test_reschedule_multiple_missed_tasks():
    """Test 5: Multiple missed tasks are redistributed in priority order."""
    today = date(2026, 10, 8)
    subjects = [
        Subject("Math", today + timedelta(days=3), 5),
        Subject("Python", today + timedelta(days=8), 2),
    ]
    blocks = [
        StudyBlock(today - timedelta(days=1), "Python", 2.0, completed=False),
        StudyBlock(today - timedelta(days=1), "Math", 2.0, completed=False),
    ]

    res = reschedule_missed_tasks(
        blocks, available_hours_per_day=2.0, subjects=subjects, today=today
    )

    assert res["rescheduled_hours"] == 4.0
    # Math (higher priority) should be scheduled on today before Python
    today_blocks = {b.subject: b.hours for b in res["schedule"] if b.date == today}
    assert today_blocks.get("Math", 0) > today_blocks.get("Python", 0)


def test_reschedule_no_future_capacity():
    """Test 6: Reports unallocated hours when missed work cannot fit before exam."""
    today = date(2026, 10, 8)
    # Math exam is TOMORROW (2026-10-09). Only today & tomorrow are available.
    math = Subject("Math", today + timedelta(days=1), 5)
    blocks = [
        # Missed 10 hours from past
        StudyBlock(today - timedelta(days=1), "Math", 10.0, completed=False),
    ]

    # Max available capacity = 2.0h/day for 2 days = 4.0h total capacity
    res = reschedule_missed_tasks(
        blocks, available_hours_per_day=2.0, subjects=[math], today=today
    )

    assert res["rescheduled_hours"] == 4.0
    assert res["unallocated_hours"] == 6.0


def test_reschedule_exam_boundary():
    """Test 7: Rescheduled tasks are never placed after the subject's exam date."""
    today = date(2026, 10, 8)
    exam_day = today + timedelta(days=1)
    math = Subject("Math", exam_day, 5)
    blocks = [
        StudyBlock(today - timedelta(days=1), "Math", 4.0, completed=False),
    ]

    res = reschedule_missed_tasks(
        blocks, available_hours_per_day=2.0, subjects=[math], today=today
    )

    for block in res["schedule"]:
        if block.subject == "Math" and not block.completed:
            assert block.date <= exam_day, f"Task scheduled after exam date: {block.date} > {exam_day}"


# =====================================================================
# 5. INTEGRATION TEST
# =====================================================================

def test_full_integration_flow():
    """Integration test verifying full flow from validation -> scheduler -> progress -> adaptive rescheduling."""
    today = date(2026, 10, 8)
    raw_subjects = [
        Subject("Mathematics", today + timedelta(days=4), 5),
        Subject("Physics", today + timedelta(days=6), 4),
    ]

    # 1. Input Validation
    validated = validate_subjects(raw_subjects, today=today)
    assert len(validated) == 2

    # 2. Call Member A's generate_schedule()
    schedule = generate_schedule(validated, available_hours_per_day=4.0, start_date=today)
    assert len(schedule) > 0

    # 3. Calculate initial progress (0%)
    prog1 = calculate_progress(schedule)
    assert prog1["progress_percentage"] == 0.0

    # 4. Mark first day blocks completed
    for block in schedule:
        if block.date == today:
            block.completed = True

    prog2 = calculate_progress(schedule)
    assert prog2["completed_hours"] > 0.0

    # 5. Advance time to day 3 (today + 2 days). Day 2 (tomorrow) block was missed (completed=False).
    day3 = today + timedelta(days=2)

    # Reschedule with available capacity per day = 5.0h (allowing 1.0h extra per day for missed work)
    rescheduled = reschedule_missed_tasks(
        schedule, available_hours_per_day=5.0, subjects=validated, today=day3
    )

    assert isinstance(rescheduled["schedule"], list)
    assert rescheduled["unallocated_hours"] == 0.0
    assert rescheduled["rescheduled_hours"] == 4.0
