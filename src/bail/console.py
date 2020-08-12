import click
import json
import os

from . import __version__
from .baildriver import *

@click.command()
@click.version_option(version=__version__)
def main():
    """Scrape the WCCA site."""
    d = BailDriver()

    # Dane
    county_number = 13

    path = f"./cases/{county_number}"
    os.makedirs(path, exist_ok=True)

    cases = d.cases_for_month(county_number)
    for case in cases:
        deets = d.case_details(case, county_number=county_number)
        with open(f'{path}/{case}.json', 'w') as f:
            json.dump(deets, f)

    # For easier debugging maybe
    self = d
    from IPython import embed; embed()

    d.close()
    
