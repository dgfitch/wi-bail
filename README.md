# Wisconsin Bail statistics

Scrape the WCCA site, loading unique cases per county, and attempt to 
determine bail statistics.

Scraping with [geckodriver](https://github.com/mozilla/geckodriver) so you will need [Firefox](https://www.mozilla.org/en-US/firefox/new/).

Built with [poetry](https://python-poetry.org/), so set up a [pyenv](https://github.com/pyenv/pyenv) of >=3.7 and then:

    pip install poetry
    poetry run bail scrape

When you see:

    Suspected captcha, continue? [y/N]:

You just need to solve the captcha.

### Possible problem cases

(assume Dane County for now)

2020JO000026

### License

[This project is released under the MIT license](LICENSE.md)
