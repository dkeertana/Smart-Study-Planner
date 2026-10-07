# Smart Study Planner — Core Scheduler Backend

A deterministic, rule-based scheduling engine built for university students to automatically generate daily study timetables based on subject difficulty and exam dates.

---

## 🧠 Scheduler Logic

The engine ranks study priorities using a simple rule-based formula:

$$\text{Priority} = \text{Difficulty} \times \text{Urgency}$$

- **Urgency**: Calculated as $\text{Urgency} = \frac{1}{\text{Days Remaining} + 1}$.
  - Exam Today ($0$ days left) $\rightarrow$ $\text{Urgency} = 1.0$ (highest priority).
  - Exam Tomorrow ($1$ day left) $\rightarrow$ $\text{Urgency} = 0.5$.
- **Difficulty**: Student rating from 1 (easiest) to 5 (hardest).
- **Daily Capacity Constraint**: Total scheduled study hours on any single day **never** exceed the student's `available_hours_per_day`.
- **Granular Allocation**: Allocates study time in clean, human-readable 0.5-hour increments.
- **Determinism**: Identical inputs always produce the exact same schedule with zero randomness.

---

## 📁 Project Structure

```text
smart-study-planner/
├── app.py                  # Streamlit UI integration stub
├── scheduler.py            # Core scheduling engine
├── models.py               # Data models (Subject, StudyBlock)
├── utils.py                # Input validation and date helpers
├── requirements.txt        # Dependencies
├── README.md               # Documentation
└── tests/
    └── test_scheduler.py   # Pytest test suite (9 tests)
```

---

## ⚡ Quickstart & Testing

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Run Test Suite
```bash
pytest
```

### 3. Usage Example for `app.py`
```python
from datetime import date, timedelta
from models import Subject
from scheduler import generate_schedule

subjects = [
    Subject(name="Mathematics", exam_date=date.today() + timedelta(days=5), difficulty=5),
    Subject(name="Physics", exam_date=date.today() + timedelta(days=8), difficulty=4),
]

schedule = generate_schedule(subjects, available_hours_per_day=4.0)

for block in schedule:
    print(f"{block.date} | {block.subject}: {block.hours}h (Completed: {block.completed})")
```
