import streamlit as st
from streamlit_calendar import calendar
from openai import OpenAI
from ics import Calendar, Event
from dotenv import load_dotenv
import os
import json
from datetime import datetime

# Load API key from .env file
load_dotenv()
api_key = os.getenv("OPEN_AI_API")

# Instantiate the OpenAI client
client = OpenAI(api_key=api_key)

st.title("AI-Powered Calendar Event Scheduler")

# Create the calendar component
calendar_output = calendar()

task_input = st.text_area("Enter your tasks")

if st.button("Schedule Tasks"):
    # Get current date
    current_date = datetime.now().strftime("%Y-%m-%d")
    default_start_time = "09:00"
    default_end_time = "10:00"

    # Make API call using the instantiated client
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "You are a helpful assistant that schedules tasks."},
            {
                "role": "user",
                "content": f"""
                Schedule these tasks: {task_input}

                If the user doesn't specify dates or times, use the current date ({current_date}), 
                with default start time {default_start_time} and end time {default_end_time}.

                Only respond with the JSON array in the following format, and do not include any other text:
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

    # Extract and process the response
    response_text = response.choices[0].message.content.strip()

    try:
        # Attempt to parse the response as JSON
        scheduled_tasks = json.loads(response_text)
    except json.JSONDecodeError:
        # Handle case where the response isn't valid JSON
        st.error("Failed to decode response as JSON. Here is the raw output:")
        st.text(response_text)
        st.stop()

    # Initialize an events list if it's not a list already
    if isinstance(calendar_output, dict):
        calendar_output["events"] = []

    # Display scheduled tasks in the calendar
    for task in scheduled_tasks:
        calendar_output["events"].append({
            "title": task["task_name"],
            "start": task["date"] + "T" + task["start_time"],
            "end": task["date"] + "T" + task["end_time"]
        })

    # .ics file generation
    cal = Calendar()
    for task in scheduled_tasks:
        event = Event()
        event.name = task["task_name"]
        event.begin = f"{task['date']}T{task['start_time']}"
        event.end = f"{task['date']}T{task['end_time']}"
        cal.events.add(event)

    with open("schedule.ics", "w") as f:
        f.writelines(cal)
    st.download_button("Download Schedule", "schedule.ics", file_name="schedule.ics")
