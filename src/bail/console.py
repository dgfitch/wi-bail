import click
import json
import os
import sys

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

    deets = d.case_details(case, county_number)

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

    try:
        cases = d.cases_for_year(county_number)
        for case in cases:
            case_json = f'{path}/{case}.json'
            if os.path.exists(case_json):
                click.echo(f"Case {case} in {county_number} already downloaded")
            else:
                deets = d.case_details(case, county_number)
                with open(case_json, 'w') as f:
                    json.dump(deets, f)
    except:
        ex = sys.exc_info()
        # Debug any issues because this is so slow
        self = d
        from IPython import embed; embed()

    d.close()
