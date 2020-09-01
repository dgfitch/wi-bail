# Wisconsin Bail statistics

Scrape the WCCA site, loading unique cases per county, and attempt to 
determine bail statistics.

Scraping uses [geckodriver](https://github.com/mozilla/geckodriver) so you will need [Firefox](https://www.mozilla.org/en-US/firefox/new/). Should be fairly easy to change to a different `WebDriver` implementation.

Visualizations mostly done in [Altair](https://altair-viz.github.io/).

Built with [poetry](https://python-poetry.org/).

## Setup

Set up a [pyenv](https://github.com/pyenv/pyenv) of >=3.7 and then:

    pip install poetry

## Scraping

    poetry run bail scrape --county-number 13

When you see:

    Suspected captcha, continue? [y/N]:

You just need to solve the captcha, type `y` and hit Enter.


### CAPTCHA notes

* You will have to complete a CAPTCHA at the first case, and then every 100 cases or so.
* The case search listing does not seem to require CAPTCHA.
* On average, you will end up solving 3 to 5 CAPTCHAs per 100 cases, which is 
  about 1 minute of work (mostly due to their artifical slow fade in.) For a 
  year's worth of Dane County, that's about 50.
* The face-blurring algorithm sometimes detects fire hydrant tops as human 
  faces.

### Possible problem cases

null result:

    cases/13/2020JO000026
    cases/13/2020ME000321

strange result:

    cases/13/2020CM000756


## Sqlite loading

    poetry run bail load

This gets you a semi-formatted SQLite db from all JSON files in `cases/`.

## Visualizations

    poetry run jupyter notebook

Open the URL in your browser and find the "Bail Visualizations" notebook.

## License

[This project is released under the MIT license](LICENSE.md)
