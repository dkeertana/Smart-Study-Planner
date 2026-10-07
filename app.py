from datetime import date, timedelta
import streamlit as st
from models import Subject
from scheduler import generate_schedule


def main():
    st.set_page_config(page_title="Smart Study Planner", page_icon="📚", layout="wide")
    st.title("📚 Smart Study Planner")
    st.write("Generate a personalized, rule-based study timetable for your upcoming exams.")

    st.sidebar.header("Configuration")
    available_hours = st.sidebar.number_input(
        "Daily Available Study Hours", min_value=0.5, max_value=24.0, value=4.0, step=0.5
    )

    st.header("Subject List")
    sample_subjects = [
        Subject(name="Mathematics", exam_date=date.today() + timedelta(days=5), difficulty=5),
        Subject(name="Physics", exam_date=date.today() + timedelta(days=8), difficulty=4),
        Subject(name="Python", exam_date=date.today() + timedelta(days=12), difficulty=3),
    ]

    for subj in sample_subjects:
        st.write(f"• **{subj.name}** | Exam Date: `{subj.exam_date}` | Difficulty: `{subj.difficulty}/5`")

    if st.button("Generate Timetable", type="primary"):
        try:
            schedule = generate_schedule(sample_subjects, available_hours)
            if not schedule:
                st.info("No study blocks generated.")
            else:
                st.success(f"Generated {len(schedule)} study blocks!")
                
                # Group schedule by date
                by_date = {}
                for block in schedule:
                    by_date.setdefault(block.date, []).append(block)
                
                for study_date in sorted(by_date.keys()):
                    blocks = by_date[study_date]
                    day_total = sum(b.hours for b in blocks)
                    with st.expander(f"📅 {study_date} — Total: {day_total}h", expanded=True):
                        for b in blocks:
                            st.write(f"- **{b.subject}**: `{b.hours} hours`")
        except ValueError as e:
            st.error(f"Error: {e}")


if __name__ == "__main__":
    main()
