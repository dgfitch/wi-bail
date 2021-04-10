#!/usr/bin/env python3
import click
import json
import os
from datetime import datetime, timedelta
import sys
import re
from pathlib import Path
from pony.orm import *

from . import __version__
from .baildriver import *
from .danecountyinmatesdriver import *
from .db import *
from .geocode import Geocode

@click.group(invoke_without_command=True)
@click.version_option(version=__version__)
@click.pass_context
def main(ctx):
    if ctx.invoked_subcommand is None:
        click.echo('No command chosen, starting scraper')
        scrape()

@main.command()
def console():
    """Testing console using IPython."""
    click.echo("Starting test console...")
    
    db = DB()
    from IPython import embed; embed()

@main.command()
def load_counties():
    """
    Load cases from scraped JSON into SQLite
    """
    db = DB()
    db.load_counties()

@main.command()
def load_inmates():
    """
    Load inmates from scraped JSON into SQLite
    """
    db = DB()
    db.load_inmates()

@main.command()
def fill_inmates():
    """
    Determine race of inmates in loaded database
    using WCCA scraper, along with other case info
    """
    db = DB()
    d = BailDriver()
    found = []
    not_found = []
    with db_session:
        for person in select(i for i in Inmate):
            case_numbers = set(d.court_case_number for a in person.arrests for d in a.details if d.court_case_number)
            for case in case_numbers:
                # The sheriff site leaves off the first two digits of the year,
                # which we need to reconstruct to look it up in WCCA.
                # NOTE: This is a Y3K problem, lol
                if case.startswith("9") or case.startswith("8"):
                    full_number = "19" + case
                else:
                    full_number = "20" + case

                # Try to find it in the DB
                cases = list(select(
                    c for c in Case
                    if c.case_number == full_number))
                if cases:
                    case = cases[0]
                else:
                    details = d.case_details(full_number, 13)

                    if not details:
                        not_found.append(full_number)
                        continue

                    # Cache it to the JSON directory for later use
                    case_json = f'./cases/13/{case}.json'
                    with open(case_json, 'w') as f:
                        json.dump(details, f)
                    
                    case = db.load_case(details, full_number, 13)

                found.append(full_number)

                case.inmate = person
                if case.race and not person.race:
                    person.race = case.race

    click.echo(f"Found {len(found)} cases with {len(not_found)} not found in WCCA, likely older cases")

@main.command()
def geocode_load():
    """
    Load geocoded addresses from cached JSON into SQLite
    """
    db = DB()
    gc = Geocode(db)
    gc.load()

@main.command()
@click.option('--start', default=1, help='County number to start at')
@click.option('--stop', default=72, help='County number to end at')
def geocode(start, stop):
    """
    Attempt to geocode addresses missing lat/lon
    """
    db = DB()
    gc = Geocode(db)
    gc.geocode(start, stop)

@main.command()
def geocode_save():
    """
    Dump geocoded addresses from SQLite into JSON
    """
    db = DB()
    gc = Geocode(db)
    gc.save()

@main.command()
@click.option('--county-number', default=13, help='County number')
def query(county_number):
    """Query cases in SQLite."""
    db = DB()
    cases = db.cases_in_county(county_number)
    from IPython import embed; embed() 

@main.command()
@click.option('--start', default=1, help='County number to start at')
@click.option('--stop', default=72, help='County number to end at')
@click.option('--year', default=2019, help='Force retry failures')
@click.option('--force', default=False, help='Force retry failures')
def scrape_wcca(start, stop, year, force):
    """Scrape the WCCA site."""

    d = BailDriver()

    def helper(county_number):
        path = f"./cases/{county_number}"
        os.makedirs(path, exist_ok=True)

        click.echo(f"Scraping county {county_number}")
        count = 0

        try:
            cases_list = f'{path}/{year}.json'
            if os.path.exists(cases_list):
                click.echo(f"Loading cached case list for county {county_number}")
                with open(cases_list) as f:
                    cases = json.load(f)
            else:
                click.echo(f"Scraping case list for county {county_number}")
                cases = d.cases_for_year(county_number, year)
                with open(cases_list, 'w') as f:
                    json.dump(list(cases), f)

            county_case_total = len(cases)
            for case in cases:
                case_json = f'{path}/{case}.json'
                failure_json = f'{path}/{case}.failure'
                if os.path.exists(case_json):
                    click.echo(f"Case {case} in {county_number} already downloaded")
                elif os.path.exists(failure_json) and not force:
                    click.echo(f"Case {case} in {county_number} already failed (use --force to retry)")
                else:
                    count += 1
                    if count % 100 > 95:
                        click.echo(f"At {count} of {county_case_total}, expecting captcha soon")
                    deets = d.case_details(case, county_number)
                    if deets == None:
                        # Track failures for now
                        failure = f'{path}/{case}.failure'
                        Path(failure).touch()
                    else:
                        with open(case_json, 'w') as f:
                            json.dump(deets, f)
        except:
            ex = sys.exc_info()
            import traceback
            print(traceback.format_exc())

            # Debug any issues interactively
            self = d
            from IPython import embed; embed()

    for county in range(start, stop + 1):
        helper(county)

    d.close()

@main.command()
@click.option('--force', '-f', is_flag=True, help='Force downloads')
@click.option('--example_url', default=None, help='Override loop and provide a single inmate URL')
def scrape_inmates(example_url, force):
    """
    Scrape Dane County inmate database
    """
    d = DaneCountyInmatesDriver()

    if example_url:
        inmates = [example_url]
    else:
        inmates = d.inmates()
    path = f"./inmates/13"
    os.makedirs(path, exist_ok=True)

    long_ago = datetime.now() - timedelta(days=7)

    for url in inmates:
        # The last digits are the "name number", whatever that means
        name_number = re.search("\d+", url).group()
        inmate_json = f'{path}/{name_number}.json'
        failure_json = f'{path}/{name_number}.failure'
        if os.path.exists(failure_json) and not force:
            click.echo(f"Inmate {failure_json} already failed (use --force to retry)")
        elif not os.path.exists(inmate_json) or \
            datetime.fromtimestamp(os.path.getmtime(inmate_json)) < long_ago:
            details = d.inmate_details(url)
            if details:
                with open(inmate_json, 'w') as f:
                    json.dump(details, f)
            else:
                click.echo(f"Inmate details failed at {url} (use --force to retry)")
                Path(failure_json).touch()

    d.close()
