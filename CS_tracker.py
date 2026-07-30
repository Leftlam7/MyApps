import streamlit as st
import sqlite3
from datetime import date

st.set_page_config(
    page_title="bicep",
    page_icon="💪",
    layout="centered"
)

st.markdown("""
<link rel="manifest" href="/app/static/manifest.json">

<meta name="theme-color" content="#000000">

""", unsafe_allow_html=True)


conn = sqlite3.connect("workouts.db")
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS workouts (
    id INTEGER PRIMARY KEY,
    date TEXT,
    exercise TEXT,
    sets INTEGER,
    reps INTEGER,
    weight REAL,
    notes TEXT
)
""")

conn.commit()


st.title("💪 Calisthenics Tracker")


push_exercises = [
    "Push-ups",
    "Dips",
    "Pike Push-ups",
    "Pseudo Planche Push-ups",
    "Handstand Push-ups"
]

pull_exercises = [
    "Pull-ups",
    "Chin-ups",
    "Australian Rows",
    "Front Lever Raises"
]

leg_exercises = [
    "Squats",
    "Bulgarian Split Squats",
    "Pistol Squats",
    "Nordic Curls",
    "Calf Raises"
]

push_tab, pull_tab, legs_tab = st.tabs(
    ["Push", "Pull", "Legs"]
)

with push_tab:
    exercise = st.selectbox(
        "Exercise",
        push_exercises,
        key="push"
    )

with pull_tab:
    exercise = st.selectbox(
        "Exercise",
        pull_exercises,
        key="pull"
    )

with legs_tab:
    exercise = st.selectbox(
        "Exercise",
        leg_exercises,
        key="legs"
    )

sets = st.number_input(
    "Sets",
    min_value=1,
    step=1
)

reps = st.number_input(
    "Reps",
    min_value=1,
    step=1
)

weight = st.number_input(
    "Extra weight (kg)",
    min_value=0.0,
    step=0.5
)

notes = st.text_area("Notes")


if st.button("Save Workout"):

    cursor.execute(
        """
        INSERT INTO workouts
        (date, exercise, sets, reps, weight, notes)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            str(date.today()),
            exercise,
            sets,
            reps,
            weight,
            notes
        )
    )

    conn.commit()

    st.success("Workout saved!")


st.subheader("History")

data = cursor.execute(
    "SELECT * FROM workouts ORDER BY id DESC"
).fetchall()

st.write(data)

