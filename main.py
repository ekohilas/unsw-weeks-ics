#!/usr/bin/env python3.6
import ics
import requests
import bs4

UNSW_CALENDAR_URL = "https://student.unsw.edu.au/calendar"

def make_calendar():
    week = ics.event.Event(
        name="T#W##",
        begin="2020-08-24",
        end="2020-08-28",
        #duration={"days": 5},
        description="UNSW Term # Week ## 20##",
    )
    week.make_all_day()

    events = set()
    events.add(week)
    calendar = ics.icalendar.Calendar(
        events=events
    )

    with open("weeks.ics", "w") as f:
        f.writelines(calendar)

def table_to_grid(table):
    rows = []
    for table_row in table.find_all("tr")
        cols = table_row.find_all("td")
        row = [
            col.text
            for col in cols
        ]
        rows.append(row)

def main():
    r = requests.get(UNSW_CALENDAR_URL)
    soup = bs4.BeautifulSoup(r.text, "lxml")
    tables = soup.find_all("table")
    for table in tables:
        print(tables)

if __name__ == "__main__":
    main()
    
