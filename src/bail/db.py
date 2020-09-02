import click
import sqlite3
import json
import os
import sys
from pathlib import Path
from datetime import date, datetime

from pony.orm import *

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
    sex = Optional(str, nullable=True)
    race = Optional(str, nullable=True)
    signature_bond = Optional(float)
    cash_bond = Optional(float)
    charges = Set('Charge')
    citations = Set('Citation')

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

class GeocodedAddress(db.Entity):
    address = Required(str)
    latitude = Required(float)
    longitude = Required(float)


class DB():
    def __init__(self):
        self.path = Path("./cases")
        db.bind(provider='sqlite', filename='wcca.sqlite', create_db=True)
        db.generate_mapping(create_tables=True)

    def load(self):
        """
        Iterate over counties in path
        """
        for d in self.path.iterdir():
            county_number = d.stem
            self.load_county(county_number)

    @db_session
    def load_county(self, county_number):
        """
        Iterate over counties in path
        """
        files = [x for x in self.path.glob(f"{county_number}/*.json")]
        for f in files:
            if f.stem == "last_year":
                continue
            click.echo(f"Importing case data from {f}")
            with open(f) as h:
                case = json.load(h)

            n = Case(
                case_number=f.stem,
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

    @db_session
    def cases_in_county(self, county_number):
        return select(
            c for c in Case
            if c.county_number == int(county_number))

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


