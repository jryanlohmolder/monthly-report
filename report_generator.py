from datetime import date, timedelta, datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import calendar
import os
import smtplib

from dotenv import load_dotenv
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

import yaml


load_dotenv()

GMAIL_ADDRESS = os.getenv("GMAIL_ADDRESS")
APP_PASSWORD = os.getenv("APP_PASSWORD")
TO_ADDRESS = os.getenv("TO_ADDRESS")
TASK_LIST_ID = os.getenv("TASK_LIST_ID")


def check_if_first_saturday(todays_date):
    """
    Check whether a given date is the first Saturday of the month.

    Args:
        todays_date (date): The date to evaluate.

    Returns:
        bool: True if the date is the first Saturday of the month, False otherwise.
    """
    return todays_date.weekday() == 5 and todays_date.day <= 7


def load_dates_file():
    """
    Load and parse the dates.yaml file from the current directory.

    Returns:
        list: A list of date entries parsed from the YAML file.

    Raises:
        yaml.YAMLError: If the file cannot be parsed.
    """
    with open("dates.yaml", "r") as file:
        try:
            data = yaml.safe_load(file)
            return data
        except yaml.YAMLError as e:
            print(f"Error parsing YAML file: {e}")
            raise


def set_date_window(todays_date):
    """
    Calculate a 40-day window starting from the given date.

    Args:
        todays_date (date): The start of the window.

    Returns:
        tuple[date, date]: The start date and end date of the window.
    """
    start = todays_date
    end = start + timedelta(days=40)

    return start, end


def filter_dates(data, start_date, end_date):
    """
    Filter date entries to those falling within the given date window.

    Ignores the year stored in each entry and assigns the current year,
    or next year if the month/day has already passed the window start.

    Args:
        data (list): List of date entries loaded from the YAML file.
        start_date (date): Start of the date window.
        end_date (date): End of the date window.

    Returns:
        list: Entries whose dates fall within the window, with the date
              field replaced by a resolved date object.
    """
    upcoming_dates = []

    current_month = start_date.month
    current_year = start_date.year

    for entry in data:
        date_str = entry["date"]
        month = int(date_str[5:7])
        stripped_date = date_str[5:]

        # Handle year rollover when current month is December and entry is in January
        if current_month == 12 and month == 1:
            year = str(current_year + 1)
            revised_date = year + "-" + stripped_date
        else:
            revised_date = str(current_year) + "-" + stripped_date

        parsed_date = datetime.strptime(revised_date, "%Y-%m-%d").date()

        if start_date <= parsed_date <= end_date:
            entry["date"] = parsed_date
            upcoming_dates.append(entry)

    return upcoming_dates


def generate_report(upcoming_dates):
    """
    Generate an HTML report listing upcoming dates sorted chronologically.

    Args:
        upcoming_dates (list): Filtered list of date entries.

    Returns:
        str: An HTML string containing the formatted report.
    """
    sorted_dates = sorted(upcoming_dates, key=lambda entry: entry["date"])

    report_lines = []
    report_lines.append("<h1 style='text-align:center'>Monthly Report</h1>")
    report_lines.append("<h2><u>Upcoming Dates</u></h2>")
    report_lines.append("<ul>")

    for entry in sorted_dates:
        formatted_date = entry["date"].strftime("%m/%d")
        line = f"<li><b>{entry['name']}</b> ({entry['type']}) - {formatted_date}</li>"
        report_lines.append(line)

    report_lines.append("</ul>")

    return "\n".join(report_lines)


def generate_calendar(upcoming_dates, start_date, end_date):
    """
    Generate an HTML calendar displaying upcoming dates within the window.

    Renders the full current month and, if the window extends into the next
    month, a partial view of that month up to the end date.

    Args:
        upcoming_dates (list): Filtered list of date entries.
        start_date (date): Start of the date window.
        end_date (date): End of the date window.

    Returns:
        str: An HTML string containing one or two calendar month tables.
    """
    weekday_headers = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]

    def build_month_table(year, month, cutoff_day=None):
        """
        Build an HTML table for a single calendar month.

        Args:
            year (int): The year of the month to render.
            month (int): The month to render (1-12).
            cutoff_day (int, optional): If provided, days beyond this number
                are rendered as empty cells. Used for partial next-month display.

        Returns:
            str: An HTML string for the month table.
        """
        month_grid = calendar.monthcalendar(year, month)
        month_name = calendar.month_name[month]

        html = [f"<h3>{month_name} {year}</h3>"]
        html.append(
            "<table border='1' cellpadding='5' "
            "style='border-collapse:collapse; width:100%'>"
        )

        # Header row with weekday names
        html.append("<tr>")
        for day_name in weekday_headers:
            html.append(f"<th>{day_name}</th>")
        html.append("</tr>")

        # One row per week
        for week in month_grid:
            html.append("<tr>")
            for day_num in week:
                # Days outside the month are represented as 0
                if day_num == 0:
                    html.append("<td></td>")
                    continue

                # Blank out days beyond the cutoff for partial months
                if cutoff_day is not None and day_num > cutoff_day:
                    html.append("<td></td>")
                    continue

                # Populate cell with day number and any matching entries
                cell_content = f"<b>{day_num}</b>"
                for entry in upcoming_dates:
                    if (
                        entry["date"].year == year
                        and entry["date"].month == month
                        and entry["date"].day == day_num
                    ):
                        cell_content += f"<br>{entry['name']} ({entry['type']})"

                html.append(f"<td>{cell_content}</td>")
            html.append("</tr>")

        html.append("</table>")
        return "\n".join(html)

    calendar_html = []

    current_month_table = build_month_table(start_date.year, start_date.month)
    calendar_html.append(current_month_table)

    # Add partial next month if the window crosses a month boundary
    if end_date.month != start_date.month:
        next_month_table = build_month_table(
            end_date.year, end_date.month, cutoff_day=end_date.day
        )
        calendar_html.append(next_month_table)

    return "\n".join(calendar_html)


def send_email(report, calendar):
    """
    Send the monthly report and calendar as an HTML email.

    Args:
        report (str): HTML string of the upcoming dates report.
        calendar (str): HTML string of the calendar view.

    Raises:
        smtplib.SMTPAuthenticationError: If login credentials are invalid.
        smtplib.SMTPException: If any other SMTP protocol error occurs.
        Exception: If an unexpected error occurs during sending.
    """
    msg = MIMEMultipart()
    msg["From"] = GMAIL_ADDRESS
    msg["To"] = TO_ADDRESS
    msg["Subject"] = "Monthly Report"

    full_html = report + "\n" + calendar
    msg.attach(MIMEText(full_html, "html"))

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
            smtp.login(GMAIL_ADDRESS, APP_PASSWORD)
            smtp.sendmail(GMAIL_ADDRESS, [TO_ADDRESS], msg.as_string())
        print("Email sent successfully.")
    except smtplib.SMTPAuthenticationError:
        print("Authentication failed. Check your GMAIL_ADDRESS and APP_PASSWORD.")
        raise
    except smtplib.SMTPException as e:
        print(f"SMTP error occurred: {e}")
        raise
    except Exception as e:
        print(f"Unexpected error sending email: {e}")
        raise


def authenticate_google_tasks():
    """
    Authenticate to the Google Tasks API using a stored refresh token.

    Reads credentials from environment variables and exchanges the refresh
    token for a fresh access token automatically.

    Returns:
        Resource: An authenticated Google Tasks API client.
    """
    creds = Credentials(
        token=None,
        refresh_token=os.environ["GOOGLE_REFRESH_TOKEN"],
        client_id=os.environ["GOOGLE_CLIENT_ID"],
        client_secret=os.environ["GOOGLE_CLIENT_SECRET"],
        token_uri="https://oauth2.googleapis.com/token",
    )

    service = build("tasks", "v1", credentials=creds)
    return service


def task_already_exists(service, title):
    """
    Check whether a task with the given title already exists in the task list.

    Args:
        service (Resource): An authenticated Google Tasks API client.
        title (str): The task title to search for.

    Returns:
        bool: True if a matching task is found, False otherwise.
    """
    result = service.tasks().list(tasklist=TASK_LIST_ID).execute()
    existing_tasks = result.get("items", [])

    for task in existing_tasks:
        if task["title"] == title:
            return True

    return False


def create_task(service, title, due_date):
    """
    Create a new task in the Google Tasks list with the given title and due date.

    Args:
        service (Resource): An authenticated Google Tasks API client.
        title (str): The title for the new task.
        due_date (date): The due date for the task.
    """
    # Google Tasks requires ISO 8601 format with time component
    formatted_date = due_date.strftime("%Y-%m-%dT00:00:00.000Z")

    task_dict = {
        "title": title,
        "due": formatted_date,
    }

    service.tasks().insert(tasklist=TASK_LIST_ID, body=task_dict).execute()


if __name__ == "__main__":
    today = date.today()

    if check_if_first_saturday(today):
        dates = load_dates_file()
        start_date, end_date = set_date_window(today)
        upcoming_dates = filter_dates(dates, start_date, end_date)

        report = generate_report(upcoming_dates)
        report_calendar = generate_calendar(upcoming_dates, start_date, end_date)
        send_email(report, report_calendar)

        service = authenticate_google_tasks()

        for entry in upcoming_dates:
            reminder_date = entry["date"] - timedelta(days=7)
            task_title = f"{entry['name']} ({entry['type']})"

            if not task_already_exists(service, task_title):
                create_task(service, task_title, reminder_date)