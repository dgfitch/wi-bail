import time
import itertools
import re
from datetime import date, timedelta

import click
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException, WebDriverException, UnexpectedAlertPresentException
import geckodriver_autoinstaller


class BailDriver:
    def __init__(self):
        geckodriver_autoinstaller.install()

        self.driver = webdriver.Firefox()
        self.driver.implicitly_wait(2)

    def test(self):
        self.driver.get("http://www.python.org")
        assert "Python" in self.driver.title
        return self.driver.title

    def get_charges(self):
        header = self.driver.find_element_by_xpath(f'//h4[text()="Charges"]')
        table = header.parent.find_element_by_tag_name("table")
        charges = table.find_elements_by_tag_name("tr")

        # First row is the header
        charges = charges[1:]

        for charge in charges:
            details = charge.find_elements_by_tag_name("td")
            if details:
                count_number = details[0].text
                statute = details[1].text
                description = details[2].text
                severity = details[3].text
                disposition = details[4].text
                yield {
                    'count_number': count_number,
                    'statute': statute,
                    'description': description,
                    'severity': severity,
                    'disposition': disposition
                }

    def get_citations(self):
        header = self.driver.find_element_by_xpath(f'//h4[text()="Charges"]')
        citations = header.parent.find_elements_by_class_name("citation")

        for citation in citations:
            yield {
                'bond_amount': self.get_dd_in(citation, "Bond amount"),
                'violation_date': self.get_dd_in(citation, "Violation date"),
                'mph_over': self.get_dd_in(citation, "MPH over"),
                'charge_description': self.get_dd_in(citation, "Charge description"),
                'severity': self.get_dd_in(citation, "Severity"),
                'ordinance_or_statute': self.get_dd_in(citation, "Ordinance or statute"),
                'statute': self.get_dd_in(citation, "Statute")
            }

    def get_dd_in(self, thing, dt_text):
        """Given an element and the definition title, find the following value"""
        try:
            dd = thing.find_element_by_xpath(f'//dt[text()="{dt_text}"]/following-sibling::dd')
            return dd.text
        except NoSuchElementException:
            return None

    def get_dd(self, dt_text):
        """Given the definition title, find the following value"""
        return self.get_dd_in(self.driver, dt_text)

    def get_race(self):
        """Look up race, which is different than above because the dt has a info icon in a span in it"""
        try:
            dd = self.driver.find_element_by_xpath(f'//dt/span/following::dd')
            return dd.text
        except NoSuchElementException:
            return None

    def get_matching_text(self, string):
        return self.driver.find_elements_by_xpath(f"//*[contains(text(), '{string}')]")

    def get_bail(self, string):
        elements = self.get_matching_text(string)
        dollaz = re.compile(r"\$[0-9.,]+")
        if len(elements) > 0:
            recent = elements[0]
            # First look in this row
            row = recent.find_element_by_xpath('./ancestor::tr')
            bail_details = row.text 
            match = dollaz.search(bail_details)
            if match:
                return match.group()

            # Otherwise look in the row after, which may be the "additional text"
            bail_details = recent.find_elements_by_xpath('./ancestor::tr/following-sibling::tr')
            if bail_details:
                match = dollaz.search(bail_details[0].text)
                if match:
                    return match.group()
            else:
                click.echo(f"Warning: could not find bail for {string}")

        return None

    def case_details(self, case_number, county_number, depth=0):
        url = f"https://wcca.wicourts.gov/caseDetail.html?caseNo={case_number}&countyNo={county_number}&mode=details"
        loaded = False
        while not loaded:
            try:
                self.driver.get(url)
                loaded = True
            except (WebDriverException, UnexpectedAlertPresentException) as e:
                click.echo(f"Error {e} loading url {url}, retrying after 2 seconds...")
                time.sleep(2)

        click.echo(f"Case {case_number} in county {county_number} loaded, trying to fetch...")
        time.sleep(5)

        # First, check for captcha
        # Sometimes this is throwing a "failed to interpret value as array",
        # but that might have been due to a stack overflow-ish repeat
        find_captcha = self.driver.find_elements_by_xpath("//iframe[@title='recaptcha challenge']")
        if len(find_captcha) > 0:
            if find_captcha[0].is_displayed():
                click.confirm('Suspected captcha, continue?')

        # Sometimes the CAPTCHA site doesn't load, so reload?
        find_warning = self.driver.find_elements_by_xpath("//strong[contains(text(), 'What is CAPTCHA?')]")
        if len(find_warning) > 0:
            if depth <= 10:
                click.echo("CAPTCHA didn't load right, retrying in 2 seconds...")
                time.sleep(2)
                return self.case_details(case_number, county_number, depth+1)
            else:
                return None

        # If no captcha found, look for "view case details" button
        # (on page with disclaimer that the case is not complete)
        view_details = self.driver.find_elements_by_xpath("//a[@class='button'][contains(text(), 'View case details')]")
        if len(view_details) > 0:
            view_details[0].click()
            time.sleep(1)

        # Look for "case not found" messages
        not_found = self.driver.find_elements_by_xpath("//h4[@class='unavailable'][contains(text(), 'That case does not exist')]")
        if len(not_found) > 0:
            click.echo(f"Case {case_number} in county {county_number} not found")
            return None


        defendant_dob = self.get_dd("Defendant date of birth")
        address = self.get_dd("Address")
        da_number = self.get_dd("DA case number")
        case_type = self.get_dd("Case type")
        filing_date = self.get_dd("Filing date")
        sex = self.get_dd("Sex")
        # Fetching race is broken again
        race = self.get_race()
        citations = []
        charges = []
        signature_bond = None
        cash_bond = None
        if case_type == "Family" or case_type == "Small Claims" or case_type == "Paternity" or case_type == "Probate" or case_type == "Civil" or case_type == "Transcript of Judgment" or case_type == "Commitment of an Inmate":
            click.echo(case_type)
        elif case_type == "Traffic Forfeiture":
            click.echo(f"Traffic")
            citations = list(self.get_citations())
        else:
            click.echo(case_type)
            charges = list(self.get_charges())
            signature_bond = self.get_bail("Signature bond set")
            cash_bond = self.get_bail("Cash bond set")

        return {
            'url': url,
            'defendant_dob': defendant_dob,
            'address': address,
            'da_number': da_number,
            'case_type': case_type,
            'filing_date': filing_date,
            'sex': sex,
            'race': race,
            'signature_bond': signature_bond,
            'cash_bond': cash_bond,
            'charges': charges,
            'citations': citations,
        }

    def date_format(self, date):
        return date.strftime("%m-%d-%Y")

    def calendar_cases(self, county_number, date):
        date1 = self.date_format(date - timedelta(days = 6))
        date2 = self.date_format(date)
        url = f"https://wcca.wicourts.gov/courtOfficialCalendarReport.html?countyNo={county_number}&dateRange.start={date1}&dateRange.end={date2}&isCourtCal=true"
        loaded = False
        while not loaded:
            try:
                self.driver.get(url)
                loaded = True
            except (WebDriverException, UnexpectedAlertPresentException) as e:
                click.echo(f"Error {e} loading url {url}, retrying after 2 seconds...")
                time.sleep(2)

        cases = self.driver.find_elements_by_class_name("case-link")
        return [c.text for c in cases]

    def weeks_past_year(self):
        start = date.today()
        d = start
        while (start - d).days < 365:
            yield d
            d -= timedelta(days = 7)



    def cases_for_dates(self, county_number, dates):
        # I'd like to do this as a comprehension but it throws
        # too many random errors.
        def generate_cases():
            for d in dates:
                try:
                    yield self.calendar_cases(county_number, d) 
                except (WebDriverException, UnexpectedAlertPresentException) as e:
                    click.echo(f"Error {e} loading cases for {d}, retrying after 2 seconds...")
                    time.sleep(2)

        cases = generate_cases()

        # Flatten out and limit to unique
        return set(itertools.chain.from_iterable(cases))

    def cases_for_month(self, county_number):
        four_weeks = itertools.islice(self.weeks_past_year(), 4)
        return self.cases_for_dates(county_number, four_weeks)

    def cases_for_week(self, county_number):
        week = [next(self.weeks_past_year())]
        return self.cases_for_dates(county_number, week)

    def cases_for_year(self, county_number):
        past_year = self.weeks_past_year()
        return self.cases_for_dates(county_number, past_year)

    def close(self):
        self.driver.close()
