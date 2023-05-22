import arrow
import requests as req
from ics import Calendar
import arrow
import locale  # for setting the locale
import os
import sys
from .logger_config import setup_logger

logger = setup_logger(__name__)
locale.setlocale(locale.LC_ALL, 'fr_FR.UTF-8')  # set the locale
filename = os.path.join(os.path.dirname(__file__), '../files/calendar.ics')

def download_calendar(url):
    # Ensure the directory for the calendar file exists
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    
    # Send a GET request to the calendar URL
    response = req.get(url)
    
    # If the response status code is 200 (successful), write the response content to the calendar file
    if response.status_code == 200:
        try:
            with open(filename, 'wb+') as file:
                logger.info(f"Writing calendar file to {filename}")
                file.write(response.content)
        except Exception as e:
            logger.error(f"Error writing calendar file: {e}")
    logger.info(f"Calendar file downloaded successfully")

def parse_calendar(start_date, end_date):
    # Open the calendar file and read its contents into a Calendar object
    try:
        with open(filename, 'r') as calendar_file:
            logger.info(f"Reading calendar file from {filename}")
            calendar = Calendar(calendar_file.read())
    except Exception as e:
        logger.error(f"Error reading calendar file: {e}")
    logger.info(f"Calendar file parsed successfully")
    
    # Convert the input start and end dates (in 'YYYY-MM-DD' format) to arrow date objects
    start_date = arrow.get(start_date, 'YYYY-MM-DD').date()
    end_date = arrow.get(end_date, 'YYYY-MM-DD').date()

    # Create a list of events that start on or between the start and end dates
    events = [event for event in calendar.events if start_date <= event.begin.date() <= end_date]

    # Return the list of filtered events
    return events