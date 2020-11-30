#!/usr/bin/env python3
import click
import json
import os
import sys
import re
from pathlib import Path

from . import __version__
from .baildriver import *
from .danecountyinmatesdriver import *
from .db import DB
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
    
    """
    d = BailDriver()

    # Dane
    county_number = 13
    case = "2020CM001458"

    deets = d.case_details(case, county_number)

    self = d
    """

    db = DB()
    from IPython import embed; embed()

@main.command()
def load():
    """
    Load cases from scraped JSON into SQLite
    """
    db = DB()
    db.load()

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
def scrape(start, stop, year, force):
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
def scrape_inmates():
    """
    Scrape Dane County inmate database
    """
    d = DaneCountyInmatesDriver()
    inmates = d.inmates()
    path = f"./inmates/13"
    os.makedirs(path, exist_ok=True)

    for url in inmates:
        # The last digits are the "name number", whatever that means
        name_number = re.search("\d+", url).group()
        inmate_json = f'{path}/{name_number}.json'
        failure_json = f'{path}/{name_number}.failure'
        if os.path.exists(inmate_json):
            click.echo(f"Inmate {inmate_json} already downloaded")
        elif os.path.exists(failure_json) and not force:
            click.echo(f"Inmate {failure_json} already failed (use --force to retry)")
        else:
            details = d.inmate_details(url)
            with open(inmate_json, 'w') as f:
                json.dump(details, f)

    d.close()
