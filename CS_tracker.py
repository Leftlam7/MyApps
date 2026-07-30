import streamlit as st
import sqlite3
from datetime import date

##  Configuring the page
st.set_page_config(
    page_title="bicep",
    page_icon="💪",
    layout="centered"
)

#accept html
st.markdown("""
<link rel="manifest" href="/app/static/manifest.json">

<meta name="theme-color" content="#000000">

""", unsafe_allow_html=True)

# Connecting to the database
conn = sqlite3.connect("workouts.db")
cursor = conn.cursor() #create cursor

#create SQLite table workouts
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

conn.commit() #saves changes after creating table

#create SQLite exersise table
cursor.execute("""
CREATE TABLE IF NOT EXISTS exercises (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE,
    category TEXT
)
""")

conn.commit()

default_exercises = [
    ("Push-ups", "Push"),
    ("Dips", "Push"),
    ("Pike Push-ups", "Push"),
    ("Pseudo Planche Push-ups", "Push"),
    ("Handstand Push-ups", "Push"),

    ("Pull-ups", "Pull"),
    ("Chin-ups", "Pull"),
    ("Australian Rows", "Pull"),
    ("Front Lever Raises", "Pull"),

    ("Squats", "Legs"),
    ("Bulgarian Split Squats", "Legs"),
    ("Pistol Squats", "Legs"),
    ("Nordic Curls", "Legs"),
    ("Calf Raises", "Legs"),
]

cursor.executemany(
    """
    INSERT OR IGNORE INTO exercises (name, category)
    VALUES (?, ?)
    """,
    default_exercises,
)

conn.commit()


st.title("💪 Calisthenics Tracker")

push_exercises = [
    row[0]
    for row in cursor.execute(
        "SELECT name FROM exercises WHERE category='Push'"
    ).fetchall()
]

pull_exercises = [
    row[0]
    for row in cursor.execute(
        "SELECT name FROM exercises WHERE category='Pull'"
    ).fetchall()
]

leg_exercises = [
    row[0]
    for row in cursor.execute(
        "SELECT name FROM exercises WHERE category='Legs'"
    ).fetchall()
]

push_tab, pull_tab, legs_tab = st.tabs(["Push", "Pull", "Legs"])

with push_tab:
    exercise = st.selectbox("Exercise", push_exercises, key="push")

with pull_tab:
    exercise = st.selectbox("Exercise", pull_exercises, key="pull")

with legs_tab:
    exercise = st.selectbox("Exercise", leg_exercises, key="legs")

sets = st.number_input("Sets", min_value=1, step=1)

reps = st.number_input("Reps", min_value=1, step=1)

weight = st.number_input("Extra weight (kg)", min_value=0.0, step=0.5)

notes = st.text_area("Notes")

#a new row is aded when saved
if st.button("Save Workout"):
    cursor.execute(
        """INSERT INTO workouts (date, exercise, sets, reps, weight, notes)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (str(date.today()), exercise, sets, reps, weight, notes)
    )
    conn.commit() #saves permantly
    st.success("Workout saved!")


st.subheader("History")

data = cursor.execute(
    "SELECT * FROM workouts ORDER BY id DESC"
).fetchall()

st.write(data)

st.divider()

st.subheader("Manage Exercises")

new_name = st.text_input("Exercise name")

new_category = st.selectbox(
    "Category",
    ["Push", "Pull", "Legs"]
)

if st.button("Add Exercise"):
    cursor.execute(
        """
        INSERT OR IGNORE INTO exercises (name, category)
        VALUES (?, ?)
        """,
        (new_name, new_category),
    )

    conn.commit()
    st.success("Exercise added!")

exercise_data = cursor.execute(
    """
    SELECT name, category
    FROM exercises
    ORDER BY category, name
    """
).fetchall()

st.table(exercise_data)
