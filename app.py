import streamlit as st
from streamlit_calendar import calendar
from openai import OpenAI
from ics import Calendar, Event
from dotenv import load_dotenv
import os
import json
from datetime import datetime, timedelta

# Load API key from .env file
load_dotenv()
api_key = os.getenv("OPEN_AI_API")

# Instantiate the OpenAI client
client = OpenAI(api_key=api_key)

st.title("Calendar Event Scheduler")

# Initialize or update the events list
if 'events' not in st.session_state:
    st.session_state.events = []

# Input fields for manual task entry
task_name = st.text_input("Task Name")
task_date = st.date_input("Task Date", value=datetime.now().date())
start_time = st.time_input("Start Time", value=datetime.now().time())
end_time = st.time_input("End Time", value=(datetime.now() + timedelta(hours=1)).time())

# Add Task Manually
if st.button("Add Task"):
    st.session_state.events.append({
        "title": task_name,
        "start": f"{task_date}T{start_time}",
        "end": f"{task_date}T{end_time}"
    })

# Display the updated calendar with the new events
calendar(events=st.session_state.events)

# AI-Powered Scheduling
task_input = st.text_area("Enter your tasks for AI scheduling")

if st.button("Schedule Tasks with AI"):
    current_date = datetime.now().strftime("%Y-%m-%d")

    response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "You are a helpful assistant that schedules tasks for optimal productivity."},
            {
                "role": "user",
                "content": f"""
                Schedule these tasks: {task_input}

                Consider the following:
                - Allocate more time for complex tasks.
                - Schedule breaks between tasks.
                - Start with the most important tasks first.
                - Avoid scheduling tasks back-to-back without breaks.

                If the user doesn't specify dates or times, use the current date ({current_date}), 
                with default start time 09:00 AM and end time 10:00 AM.
                You will optimize for maximum productivity and efficiency wihout overloading the user's schedule.
                Have standard time for breaks, lunch and dinner. For example, the dinner should ideally be scheduled between 6:00 PM and 8:00 PM.
                The lunch should ideally be scheduled between 12:00 PM and 2:00 PM.
                breaks should be ideally be somewhere between 30 minutes to 1 hour depending on the previous task intensity and the next task intensity.
                

                Ensure that each task's end time is after its start time.

                Return the schedule in JSON format without any additional text:
                [
                    {{
                        "task_name": "Task Name",
                        "date": "YYYY-MM-DD",
                        "start_time": "HH:MM",
                        "end_time": "HH:MM"
                    }}
                ]
                """
            }
        ]
    )

    response_text = response.choices[0].message.content.strip()

    try:
        scheduled_tasks = json.loads(response_text)
    except json.JSONDecodeError:
        st.error("Failed to decode response as JSON. Here is the raw output:")
        st.text(response_text)
        st.stop()

    for task in scheduled_tasks:
        # Ensure valid times
        start_time = datetime.strptime(f"{task['date']} {task['start_time']}", "%Y-%m-%d %H:%M")
        end_time = datetime.strptime(f"{task['date']} {task['end_time']}", "%Y-%m-%d %H:%M")
        
        if end_time <= start_time:
            st.error(f"Task '{task['task_name']}' has an invalid time range. End time must be after start time.")
            continue

        st.session_state.events.append({
            "title": task["task_name"],
            "start": task["date"] + "T" + task["start_time"],
            "end": task["date"] + "T" + task["end_time"]
        })

    calendar(events=st.session_state.events)

# Generate and show the download button only if there are events
if st.session_state.events:
    cal = Calendar()
    for event in st.session_state.events:
        cal_event = Event()
        cal_event.name = event["title"]
        cal_event.begin = event["start"]
        cal_event.end = event["end"]
        cal.events.add(cal_event)

    with open("schedule.ics", "w") as f:
        f.writelines(cal)

    with open("schedule.ics", "rb") as f:
        st.download_button("Download Schedule", f, file_name="schedule.ics")
