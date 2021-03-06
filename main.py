#!/usr/bin/env python3.6
import bs4
import collections
import datetime
import dateutil.parser
import dateutil.rrule
import ics
import requests
import pprint

UNSW_CALENDAR_URL = "https://student.unsw.edu.au/calendar"
CURRENT_YEAR = datetime.datetime.now().year
ONE_WEEK = datetime.timedelta(days=6)

BREAK_WEEK = 6
PARSE_BREAK_WEEK = False
PARSE_SPECIFIC_PERIODS = False
PARSE_SUMMER_TERM = False
PARSE_TERM_BREAK = False
PARSE_WHOLE_TERM = False
SHORT_LAST_WEEK = True

class DateRangeParseError(ValueError):
    pass

def make_calendar(events):
    calendar = ics.icalendar.Calendar(
        events=events
    )
    with open("unsw.ics", "w") as f:
        f.writelines(calendar)

def table_to_grid(table):
    return [
        [
            # parse \xa0 as spaces"
            col.text.replace("\xa0", " ").strip()
            for col in table_row.find_all("td")
        ]
        for table_row in table.find_all("tr")
    ]

def create_term_week_events(term, start, end):
    weeks = set()
    for i, dt in enumerate(
        dateutil.rrule.rrule(
            dateutil.rrule.WEEKLY,
            dtstart=start,
            until=end,
        ),
        start=1,
    ):
        if i == BREAK_WEEK and not PARSE_BREAK_WEEK:
            continue
        week = create_spanning_event(
            name=f"Week {i}",
            term=term,
            begin=dt,
            end=(
                end
                if i == 10 and SHORT_LAST_WEEK
                else None
            ),
        )
        weeks.add(week)
    return weeks

def create_spanning_event(name, term, begin, end=None):
    if end is None:
        end = begin + ONE_WEEK
    event = ics.event.Event(
        name=f"{name} T{term}",
        description=f"UNSW {begin.year} Term {term} {name}",
        begin=begin,
        end=end,
    )
    event.make_all_day()
    return event

def get_years(term_tables): # dict -> list[int]
    tables = list(term_tables.values())
    table = tables[0]
    row = table[0]
    years = list(map(int, row[1:3]))
    return years

def to_years_dict(term_tables):
    years = get_years(term_tables)
    years_dict = {
        year: collections.defaultdict(dict)
        for year in years
    }
    for term, table in term_tables.items():
        # Skip header
        for row in table[1:]:
            name, *periods = row
            for year, period in zip(years, periods):
                try:
                    date_range = parse_date_range(period, year)
                except DateRangeParseError as e:
                    print(e)
                    continue
                years_dict[year][term][name] = date_range
    return years_dict

def parse_date_range(date_range, year):
    """
    "8 Feb 2020"
    "6 Feb"
    "4 Jan - 6 Feb"
    "19 Dec 2020 - 3 Jan 2021"
    "N/A"
    """

    dates = date_range.split(" - ")
    year_dt = datetime.date.today().replace(year=year)
    if not 1 <= len(dates) <= 2:
        raise DateRangeParseError(f"Unexpected date range '{date_range}'")
    try:
        start = dateutil.parser.parse(dates[0], default=year_dt)
        end = start
        if len(dates) == 2:
            end = dateutil.parser.parse(dates[1], default=year_dt)
    except ValueError as e:
        raise DateRangeParseError(f"Couldn't parse date range '{date_range}'") from e
    return (start, end)

def parse_terms_as_tables(tables):
    return {
        table.find_previous("h2").text: table_to_grid(table)
        for table in tables
    }

def create_events_from_terms(terms):
    events = set()
    for term, periods in terms.items():

        if term.startswith("Summer"):
            if not PARSE_SUMMER_TERM:
                continue
            raise NotImplementedError

        # 'Term 1' -> 1
        term = int(term.split()[-1])
        for name, (start, end) in periods.items():

            if name.startswith("Teaching period"):
                if name.endswith(("A", "B", "C")):
                    if not PARSE_SPECIFIC_PERIODS:
                        continue
                    raise NotImplementedError
                # Normal teaching periods
                events.update(create_term_week_events(term, start, end))

            elif name == f"Term {term}":
                if not PARSE_WHOLE_TERM:
                    continue
                raise NotImplementedError

            elif name == "Term break":
                if not PARSE_TERM_BREAK:
                    continue
                raise NotImplementedError

            else:
                # Flexibility Week, Study Period, Exams, O-Week
                if name.endswith(f"T{term}"):
                    name = name[:-3].title()
                events.add(create_spanning_event(name, term, start, end))
    return events

def get_tables():
    r = requests.get(UNSW_CALENDAR_URL)
    soup = bs4.BeautifulSoup(r.text, "lxml")
    tables = soup.find_all("table")
    return tables

if __name__ == "__main__":

    tables = get_tables()
    term_tables = parse_terms_as_tables(tables)
    pprint.pprint(term_tables)

    years_dict = to_years_dict(term_tables)
    years = get_years(term_tables)
    pprint.pprint(years_dict)

    if CURRENT_YEAR not in years:
        print(f"'{CURRENT_YEAR}' not in '{years}'")
        raise SystemExit

    terms = years_dict[CURRENT_YEAR]
    pprint.pprint(terms)

    events = create_events_from_terms(terms)
    pprint.pprint(events)
    make_calendar(events)
