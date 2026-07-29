import streamlit as st
import sqlite3
from datetime import date

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


exercise = st.text_input("Exercise")

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

