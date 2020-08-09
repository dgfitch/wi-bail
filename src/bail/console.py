import click

from . import __version__
from baildriver import *

@click.command()
@click.version_option(version=__version__)
def main():
    """Scrape the WCCA site."""
    d = BailDriver()
    
    deets = d.case_details("2019CF001487", county_number=13)
    click.echo(deets)

    from IPython import embed; embed()

    d.close()
    
