# Smart Study Planner — Core Engine, Supporting Logic & UI

A deterministic, rule-based scheduling and adaptive rescheduling engine built for university students to automatically generate and adapt daily study timetables based on subject difficulty and exam dates.

---

## 🧠 Core Features & Architecture

### 1. Primary Scheduler
Ranks study priorities using a simple rule-based formula:

$$\text{Priority} = \text{Difficulty} \times \text{Urgency}$$

- **Urgency**: Calculated as $\text{Urgency} = \frac{1}{\text{Days Remaining} + 1}$.
  - Exam Today ($0$ days left) $\rightarrow$ $\text{Urgency} = 1.0$ (highest priority).
  - Exam Tomorrow ($1$ day left) $\rightarrow$ $\text{Urgency} = 0.5$.
- **Difficulty**: Rating from 1 (easiest) to 5 (hardest).
- **Daily Capacity Constraint**: Total scheduled study hours on any single day **never** exceed `available_hours_per_day`.
- **Determinism**: Identical inputs always produce the exact same schedule with zero randomness.

---

### 2. Supporting Logic & Validation (`utils.py`)
- **Input Validation**: `validate_subject_name`, `validate_difficulty` (1-5), `validate_available_hours` (>0), `validate_exam_date` (rejects past dates), and `validate_subjects` (prevents duplicate subject names).
- **Date Utilities**: `days_until_exam(exam_date, today=None)` returns days remaining.
- **Dual Progress Tracking**: 
  - `calculate_daily_progress(schedule, target_date)`: Tracks today's tasks specifically ($\text{Today's Completed} / \text{Today's Planned} \times 100$). Naturally resets on a new date.
  - `calculate_progress(schedule)`: Tracks overall plan progress ($\text{Total Completed} / \text{Total Planned} \times 100$). Retains all past completed work across days.
- **Motivational Completion Feedback**: `get_motivational_message(completed_count, daily_completed, overall_progress)` triggers encouraging messages on genuine task completion without spamming on reruns.

---

### 3. Adaptive Rescheduling (`reschedule_missed_tasks`)
- **Missed Work Detection**: Identifies uncompleted study blocks whose scheduled date has passed (`block.date < today` and `completed == False`).
- **Preserves Completed Work**: Completed tasks (`completed == True`) remain untouched on their original dates.
- **Capacity & Exam Boundaries**: Redistributes missed hours into future daily available capacity up to the subject's exam date. Never schedules after an exam date or exceeds daily limits.
- **Unallocated Work Reporting**: Reports any missed work that cannot fit before an exam date.

---

## 📁 Project Structure

```text
smart-study-planner/
├── app.py                  # Streamlit UI integration reference & dual tracking
├── scheduler.py            # Core initial scheduling engine (Member A)
├── models.py               # Data models (Subject, StudyBlock)
├── utils.py                # Input validation, date helpers, progress, rescheduling
├── requirements.txt        # Minimal dependencies
├── README.md               # Project documentation
└── tests/
    ├── test_scheduler.py   # Scheduler tests (9 tests)
    └── test_utils.py       # Supporting logic, progress, rescheduling tests (20 tests)
```

---

## ⚡ Quickstart & Testing

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Run Streamlit Application
```bash
streamlit run app.py
```

### 3. Run Test Suite
```bash
pytest
```

---

## 🔌 API Integration Contract

### Dual Progress & Motivational Feedback Example
```python
from datetime import date, timedelta
from models import Subject
from scheduler import generate_schedule
from utils import (
    validate_subjects,
    calculate_progress,
    calculate_daily_progress,
    get_motivational_message,
    reschedule_missed_tasks,
)

subjects = [
    Subject("Mathematics", date.today() + timedelta(days=5), 5),
    Subject("Physics", date.today() + timedelta(days=8), 4),
]

# 1. Validate inputs & generate schedule
validated_subjects = validate_subjects(subjects)
schedule = generate_schedule(validated_subjects, available_hours_per_day=4.0)

# 2. Calculate Dual Progress Trackers
today_prog = calculate_daily_progress(schedule, target_date=date.today())
overall_prog = calculate_progress(schedule)

print(f"Today's Progress: {today_prog['progress_percentage']}%")
print(f"Overall Progress: {overall_prog['progress_percentage']}%")

# 3. Motivational message on completion
message = get_motivational_message(
    completed_count=1,
    daily_completed=today_prog["progress_percentage"] >= 100.0,
    overall_progress=overall_prog["progress_percentage"],
)
print(f"Feedback: {message}")
```
