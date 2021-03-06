from pony.orm import *
import sqlite3
import click
import json
import os
import sys
from pathlib import Path
from datetime import date, datetime

db = Database()

class Case(db.Entity):
    case_number = Required(str)
    county_number = Required(int)
    da_number = Optional(str, nullable=True)
    case_type = Required(str)
    url = Optional(str, nullable=True)
    defendant_dob = Optional(date)
    filing_date = Optional(date)
    address = Optional(str, nullable=True)
    latitude = Optional(float)
    longitude = Optional(float)
    fips = Optional(str, nullable=True)
    county_name = Optional(str, nullable=True)
    sex = Optional(str, nullable=True)
    race = Optional(str, nullable=True)
    signature_bond = Optional(float)
    cash_bond = Optional(float)
    charges = Set('Charge')
    citations = Set('Citation')
    inmate = Optional('Inmate')

class Charge(db.Entity):
    case = Required('Case')
    count_number = Optional(str)
    statute = Optional(str)
    description = Optional(str)
    severity = Optional(str)
    disposition = Optional(str)

class Citation(db.Entity):
    case = Required('Case')
    bond_amount = Optional(float)
    mph_over = Optional(str)
    charge_description = Optional(str)
    severity = Optional(str)
    ordinance_or_statute = Optional(str)
    statute = Optional(str)

class Inmate(db.Entity):
    county_number = Required(int)
    url = Optional(str)
    name = Optional(str)
    race = Optional(str)
    status = Optional(str)
    building = Optional(str)
    area = Optional(str)
    scheduled_release = Optional(str)
    booking_number = Optional(str)
    booking_date = Optional(str)
    name_number = Optional(str)
    arrests = Set('Arrest')
    cases = Set('Case')

    def days_since_booking(self):
        delta = datetime.now() - datetime.strptime(self.booking_date, "%m/%d/%Y %I:%M %p")
        return delta.days

    def most_recent_arrest(self):
        def parse_arrest_date(d):
            return datetime.strptime(d, "%m/%d/%Y %I:%M %p")

        dates = set(parse_arrest_date(d.date)
            for a in self.arrests for d in a.details if d.date)
        return max(dates)

    def days_since_most_recent_arrest(self):
        delta = datetime.now() - self.most_recent_arrest()
        return delta.days

    def case_numbers(self):
        return set(d.court_case_number for a in self.arrests for d in a.details if d.court_case_number)

class Arrest(db.Entity):
    inmate = Required('Inmate')
    date = Optional(str)
    agency = Optional(str)
    arrest_number = Optional(str)
    agency_case_number = Optional(str)
    details = Set('ArrestDetail')

class ArrestDetail(db.Entity):
    arrest = Required('Arrest')
    offense = Optional(str)
    date = Optional(str)
    disposition_date = Optional(str)
    court_case_number = Optional(str)
    court_case_url = Optional(str)
    entry_code = Optional(str)


class DB():
    def __init__(self):
        self.cases_path = Path("./cases")
        self.inmates_path = Path("./inmates")
        db.bind(provider='sqlite', filename='jail.sqlite', create_db=True)
        db.generate_mapping(create_tables=True)

    def load_counties(self):
        """
        Iterate over counties in path and load them
        """
        for d in self.cases_path.iterdir():
            county_number = d.stem
            self.load_county(county_number)

    def load_inmates(self):
        """
        Clear all arrests and inmates records, Iterate over inmates in path, and load them
        """
        Arrest.select().delete()
        Inmate.select().delete()

        for d in self.inmates_path.iterdir():
            county_number = d.stem
            self.load_inmates_for_county(county_number)

    def load_case(self, case, case_number, county_number):
        n = Case(
            case_number=case_number,
            county_number=county_number,
            da_number=case['da_number'],
            case_type=case['case_type'],
            url=case['url'],
            defendant_dob=self.to_date(case['defendant_dob']),
            filing_date=self.to_date(case['filing_date']),
            address=case['address'],
            sex=case['sex'],
            race=case['race'],
            signature_bond=self.to_float(case['signature_bond']),
            cash_bond=self.to_float(case['cash_bond']),
        )

        for c in case['citations']:
            citation = Citation(
                case=n,
                bond_amount=self.to_float(c['bond_amount']),
                mph_over=c['mph_over'],
                charge_description=c['charge_description'],
                severity=c['severity'],
                ordinance_or_statute=c['ordinance_or_statute'],
                statute=c['statute'],
            )

        for c in case['charges']:
            charge = Charge(
                case=n,
                count_number=c['count_number'],
                statute=c['statute'],
                description=c['description'],
                severity=c['severity'],
                disposition=c['disposition'],
            )

        return n

    @db_session
    def load_county(self, county_number):
        """
        Iterate over counties in path
        """
        files = [x for x in self.cases_path.glob(f"{county_number}/*.json")]
        for f in files:
            if f.stem == "last_year" or len(f.stem) == 4:
                continue
            click.echo(f"Importing case data from {f}")
            with open(f) as h:
                case = json.load(h)
                self.load_case(case, f.stem, county_number)

    @db_session
    def cases_in_county(self, county_number):
        return select(
            c for c in Case
            if c.county_number == int(county_number))

    @db_session
    def load_inmates_for_county(self, county_number):
        """
        Iterate over inmates in path
        """
        files = [x for x in self.inmates_path.glob(f"{county_number}/*.json")]
        for f in files:
            click.echo(f"Importing inmate data from {f}")
            with open(f) as h:
                i = json.load(h)

            inmate = Inmate(
                    url=i['url'],
                    county_number=county_number,
                    name=i['name'],
                    status=i['status'],
                    building=i['building'],
                    area=i['area'],
                    scheduled_release=i['scheduled_release'],
                    booking_number=i['booking_number'],
                    booking_date=i['booking_date'],
                    name_number=i['name_number'],
                )
            
            for a in i['arrests']:
                arrest = Arrest(
                    inmate=inmate,
                    date=a['date'],
                    agency=a['agency'],
                    arrest_number=a['arrest_number'],
                    agency_case_number=a['agency_case_number'],
                    )
                for ad in a['details']:
                    details = ArrestDetail(
                        arrest=arrest,
                        offense=ad['offense'],
                        date=ad['date'],
                        disposition_date=ad['disposition_date'],
                        court_case_number=ad['court_case_number'],
                        court_case_url=ad['court_case_url'] or '',
                        entry_code=ad['entry_code'],
                        )

    def to_float(self, text):
        if text == None or text.strip() == '':
            return None
        return float(text.replace("$", "").replace(",", ""))

    def to_date(self, text):
        if text == None or text.strip() == '':
            return None
        if len(text) == 7:
            return datetime.strptime(text, "%m-%Y")
        return datetime.strptime(text, "%m-%d-%Y")


