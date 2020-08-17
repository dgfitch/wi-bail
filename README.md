# Wisconsin Bail statistics

Scrape the WCCA site, loading unique cases per county, and attempt to 
determine bail statistics.

Scraping uses [geckodriver](https://github.com/mozilla/geckodriver) so you will need [Firefox](https://www.mozilla.org/en-US/firefox/new/). Should be fairly easy to change to a different `WebDriver` implementation.

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

* You will have to do a CAPTCHA at the first case, and then every 100 cases or so.
* The case search listing does not seem to ever require one.
* On average, you will end up solving 3 to 5 CAPTCHAs per 100 cases, which is 
  about 1 minute of work (mostly due to their artifical slow fade in.)
* The face-blurring algorithm sometimes detects fire hydrant tops as human 
  faces.

### Possible problem cases

null result:

    cases/13/2020JO000026.json


## Sqlite loading

    poetry run bail load --county-number 13

Still in progress, but this should get you a semi-formatted SQLite db.

## License

[This project is released under the MIT license](LICENSE.md)
