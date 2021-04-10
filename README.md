# Wisconsin Bail statistics

Scrape the WCCA site, loading unique cases per county, and attempt to 
determine bail statistics.

Scraping uses [geckodriver](https://github.com/mozilla/geckodriver) so you will need [Firefox](https://www.mozilla.org/en-US/firefox/new/). Should be fairly easy to change to a different `WebDriver` implementation.

Visualizations mostly done in [Altair](https://altair-viz.github.io/).

Built with [poetry](https://python-poetry.org/).

## Setup

Set up a [pyenv](https://github.com/pyenv/pyenv) of >=3.7 and then:

    pip install poetry
    poetry install

## Scraping Dane County inmates

In progress. To get the inmates,

    poetry run bail scrape-inmates

To load them into the SQLite DB,

    poetry run bail load-inmates

To use the below scraping WCCA stuff to find all case details and fill in 
missing inmate details like race,

    poetry run bail fill-inmates

Now, after entering some CAPTCHAs and once again confirming your membership in 
the human race, you can either look straight in the SQLite database with a 
tool of your choice or query the data with the [Pony](https://ponyorm.org/)) 
ORM by running:

    poetry run bail query

See the [EXAMPLES](EXAMPLES.md) file for some query samples.

## Scraping WCCA

To scrape a given county number (internal to WCCA, slightly out of 
alphabetical order due to Actual Historical Reasons)

    poetry run bail scrape-wcca --county-number 13

When you see:

    Suspected captcha, continue? [y/N]:

You just need to solve the captcha, type `y` and hit Enter.

Now you can load case data for any counties you downloaded:

    poetry run bail load-counties


### CAPTCHA notes

* You will have to complete a CAPTCHA at the first case, and then every 100 cases or so.
* The case search listing does not seem to require CAPTCHA.
* On average, you will end up solving 3 to 5 CAPTCHAs per 100 cases, which is 
  about 1 minute of work (mostly due to their artifical slow fade in.) For a 
  year's worth of Dane County, that's about 50.
* The face-blurring algorithm sometimes detects fire hydrant tops as human 
  faces.

## Sqlite loading

    poetry run bail load-counties

This gets you a semi-formatted SQLite db from all JSON files in `cases/`.

    poetry run bail load-inmates

Same, loads in the inmates.

## Visualizations

    poetry run jupyter notebook

Open the URL in your browser and find the "Bail Visualizations" notebook.

## License

[This project is released under the MIT license](LICENSE.md)
