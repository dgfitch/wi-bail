import click
import json
import os

from . import __version__
from .baildriver import *

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
    
    d = BailDriver()

    # Dane
    county_number = 13
    case = "2020CM001458"

    deets = d.case_details(case, county_number=county_number)

    # For easier debugging maybe
    self = d
    from IPython import embed; embed()

@main.command()
def scrape():
    """Scrape the WCCA site."""

    d = BailDriver()

    # Dane
    county_number = 13

    path = f"./cases/{county_number}"
    os.makedirs(path, exist_ok=True)

    click.echo("Loading unique cases")
    cases = d.cases_for_month(county_number)
    for case in cases:
        deets = d.case_details(case, county_number=county_number)
        with open(f'{path}/{case}.json', 'w') as f:
            json.dump(deets, f)

    d.close()
