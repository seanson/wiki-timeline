#!/usr/bin/env python
import re
import os
import json

import wikipedia
import logging
import dateparser

from bs4 import BeautifulSoup
from pprint import pprint
from tqdm import tqdm
from copy import copy

logger = logging.getLogger()
wikipedia.set_rate_limiting(False)

# This didn't really work out:
# import pywikibot
# import mwparserfromhell


DECADE = re.compile(r"^/wiki/\d{2,5}s?")
YEAR = re.compile(r"(\d+)")
DATE_PREFIX = re.compile(
    r"^((January|February|March|April|May|June|July|August|September|October|November|December) ?\d{0,2})"
)


def get_page(page, html=False):
    page = str(page)
    if not os.path.exists(".cache"):
        os.mkdir(".cache")
    if html:
        cache_path = f".cache/{page}.html"
    else:
        cache_path = f".cache/{page}.wiki"
    if os.path.exists(cache_path):
        logger.debug(f"Using cache: {cache_path}")
        with open(cache_path, "r") as cache_file:
            return cache_file.read()
    logger.debug(f"Fetching page: {page}")
    if html:
        page = wikipedia.page(title=page, auto_suggest=False)
        data = page.html()
    else:
        import pywikibot

        site = pywikibot.Site(fam="wikipedia", code="en")
        page = pywikibot.Page(site, page)
        data = page.get()
    with open(cache_path, "w") as cache_file:
        cache_file.write(data)
    return data


def extract_date(item, year):
    date_check = DATE_PREFIX.search(item)
    if date_check is None:
        return None
    date_info = dateparser.parse(f"{date_check.groups(0)[0]}, {year}")
    return date_info


def di_key(date_info):
    return f"{date_info.year}-{date_info.month:02d}-{date_info.day:02d}"


def format_item(item):
    item = str(item)
    # item = item.replace("–", "</br>")
    return item


def extract_list(events_base, item_id, year):
    results = {}
    header = events_base.find_next(id=item_id, class_="mw-headline")
    if header is None:
        logger.debug(
            f"Could not find header with id {item_id} in https://en.wikipedia.org/wiki/{year}"
        )
        return results
    ul = header.find_next("ul", recursive=False).extract()
    if ul is None:
        logger.warning(f"Could not find content for header {item_id}")
        return results
    # TODO: Scrape these later
    if item_id in ["Births", "Deaths", "Date_unknown"]:
        return results

    for li in ul.find_all("li", recursive=False):
        # Nested date management
        parseable_items = []
        sub_ul = li.find("ul", recursive=False)
        if sub_ul is None:
            parseable_items.append(li)
        else:
            sub_ul = sub_ul.extract()
            for sub_li in sub_ul.find_all("li", recursive=False):
                item = copy(li)
                item.append(" – ")
                item.append(sub_li)
                # print(list(sub_li.descendants))
                # for content in list(sub_li.descendants):
                #     if content is None:
                #         continue
                # print(type(content))
                # item.extend(content)
                # print(sub_li.contents)
                # item.append(sub_li)
                parseable_items.append(sub_li)

        for item in parseable_items:
            date_info = extract_date(item.text, year)
            if date_info is None:
                continue
            results.setdefault(date_info, [])
            results[date_info].append(format_item(item))
        # print(li.text)
    return results


def parse_year(year):
    text = get_page(year, html=True)
    bs = BeautifulSoup(text, "lxml")
    results = {}
    events = bs.find(id="Events", class_="mw-headline")
    if events is None:
        logger.error(f"No Events header found for year {year}")
        return results

    extract_list(events, "Deaths", year)
    extract_list(events, "Births", year)
    extract_list(events, "Date_unknown", year)
    results.update(extract_list(events, "January–December", year))
    results.update(extract_list(events, "July–December", year))
    results.update(extract_list(events, "January–June", year))
    if len(results) == 0:
        logger.warning(
            f"Unable to extract any events from https://en.wikipedia.org/wiki/{year}"
        )
    return results


years = {}

start = 1300
end = 1500

for year in tqdm(range(start, end)):
    get_page(year, html=True)

for year in tqdm(range(start, end)):
    result = parse_year(year)
    years.update(result)
pprint(years, width=180)

vis_items = {}
for i, key in enumerate(sorted(years.keys())):
    century = int(key.year - (key.year % 100))
    vis_items.setdefault(century, [])
    vis_items[century].append(
        {"start": di_key(key), "group": "1", "id": i, "content": "".join(years[key])}
    )


with open("timeline-frontend/src/years.json", "w") as years_file:
    century = start - (start % 100)
    json.dump(
        {"start": f"{century}-01-01", "end": f"{century+99}-12-31", "data": vis_items},
        years_file,
        indent=2,
    )

print(f"Wrote {len(vis_items)} items to years.json")
