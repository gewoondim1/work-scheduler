import datetime
from dateutil import tz
import os
import pickle
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

# If modifying these scopes, delete the file token.pickle.
SCOPES = ["https://www.googleapis.com/auth/calendar"]
CALENDARS = ["primary",
             "REDACTED"]
STARTWORK, ENDWORK = datetime.time(hour=9), datetime.time(hour=17)
STUDYTYPES = ("Self study unsupervised",
              "Self study supervised",
              "Tutorial",
              "Lectorial",
              "Q&A")


def events_between(now, end, service):
    events = []

    for calendar in CALENDARS:
        events += service.events().list(calendarId=calendar, timeMin=now.isoformat() + "Z",
                                        timeMax=end.isoformat() + "Z", singleEvents=True,
                                        orderBy="startTime").execute().get("items", [])  # "Z" indicates UTC time

    return events


def main():
    """Shows basic usage of the Google Calendar API.
    Prints the start and name of the next 10 events on the user"s calendar.
    """

    credentials = None
    # The file token.pickle stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists("token.pickle"):
        with open("token.pickle", "rb") as token:
            credentials = pickle.load(token)

    # If there are no (valid) credentials available, let the user log in.
    if not credentials or not credentials.valid:
        if credentials and credentials.expired and credentials.refresh_token:
            credentials.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
            credentials = flow.run_local_server(port=0)

        # Save the credentials for the next run
        with open("token.pickle", "wb") as token:
            pickle.dump(credentials, token)

    service = build("calendar", "v3", credentials=credentials)

    # Call the Calendar API
    now = datetime.datetime.utcnow()

    if now.month == 12:
        end = now.replace(year=now.year+1, month=1)
    else:
        end = now.replace(month=now.month+1)

    delta = end - now
    dates = set()

    for i in range(delta.days + 1):
        date = (now + datetime.timedelta(days=i)).date()
        if date.weekday() < 5:
            dates.add(date)

    events = events_between(now, end, service)

    if not events:
        print("No upcoming events found.")
    for event in events:
        event_start = event["start"].get("dateTime", event["start"].get("date"))
        event_start = datetime.datetime.strptime(event_start[:-3] + event_start[-2:], r"%Y-%m-%dT%H:%M:%S%z")

        event_end = event["end"].get("dateTime", event["end"].get("date"))
        event_end = datetime.datetime.strptime(event_end[:-3] + event_end[-2:], r"%Y-%m-%dT%H:%M:%S%z")

        if event_start.weekday() < 5:
            if not any(f"Type: {study}" in event.get("description", "") for study in STUDYTYPES):
                if STARTWORK <= event_start.time() <= ENDWORK:
                    dates.discard(event_start.date())
                elif STARTWORK <= event_end.time() <= ENDWORK:
                    dates.discard(event_end.date())

    for date in dates:
        event_start = datetime.datetime(year=date.year, month=date.month, day=date.day, hour=9, tzinfo=tz.tzlocal())
        event_end = datetime.datetime(year=date.year, month=date.month, day=date.day, hour=17, tzinfo=tz.tzlocal())

        event_body = {"summary": "Werk",
                      "location": "REDACTED",
                      "start": {"dateTime": event_start.isoformat()},
                      "end": {"dateTime": event_end.isoformat()}}

        event = service.events().insert(calendarId="primary", body=event_body).execute()
        print(f"Event created at {event.get('htmlLink')}")


if __name__ == "__main__":
    os.chdir(os.path.abspath(os.path.dirname(__file__)))

    main()
