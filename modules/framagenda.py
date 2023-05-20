import arrow
import requests
from ics import Calendar
import arrow
import locale  # for setting the locale
import os

locale.setlocale(locale.LC_ALL, 'fr_FR.UTF-8')  # set the locale

filename = os.path.join(os.path.dirname(__file__), '../files/calendar.ics')

def download_calendar(url):
    # Make sure the directory exists
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    response = requests.get(url)
    if response.status_code == 200:
        with open(filename, 'wb+') as file:
            file.write(response.content)
        print(f"Calendar downloaded and saved to {filename}")
    else:
        print("Failed to download the calendar")


def parse_calendar(start_date, end_date):
    # Load the calendar file
    with open(filename, 'r') as calendar_file:
        calendar = Calendar(calendar_file.read())

    # Convert the input dates to arrow date objects for comparison
    start_date = arrow.get(start_date, 'YYYY-MM-DD').date()
    end_date = arrow.get(end_date, 'YYYY-MM-DD').date()

    # Filter events based on start and end date
    events = [event for event in calendar.events if start_date <= event.begin.date() <= end_date]

    # Return the filtered events
    return events