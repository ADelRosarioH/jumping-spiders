import re
import datetime
from dateparser import parse

months_regex = re.compile(
    r'(enero|febrero|marzo|abril|mayo|junio|julio|agosto|septiembre|octubre|noviembre|diciembre)', re.I)
days_regex = re.compile(r'[^0-9][0-9]{2}[^0-9]')
years_regex = re.compile(r'[0-9]{4}')


def get_months(text):
    return months_regex.findall(text)


def get_days(text):
    return [digits.replace('-', '') for digits in days_regex.findall(text)]


def get_years(text):
    return years_regex.findall(text)


def get_from_date(text):
    months = get_months(text)
    days = get_days(text)
    years = get_years(text)

    month = _get_parsed_month(months[0])
    day = days[0]
    year = years[0]

    date = datetime.datetime(year=int(year), month=int(month), day=int(day))
    return date


def get_to_date(text):
    months = get_months(text)
    days = get_days(text)
    years = get_years(text)

    month = _get_parsed_month(months[1]) if len(
        months) > 1 else _get_parsed_month(months[0])
    day = days[1] if len(days) > 1 else days[0]
    year = years[1] if len(years) > 1 else years[0]

    date = datetime.datetime(year=int(year), month=int(month), day=int(day))
    return date


def _get_parsed_month(month):
    return parse(month, locales=['es-DO']).month


def get_date_range(text):
    return [get_from_date(text), get_to_date(text)]
