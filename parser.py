"""Parser for akvilon-mitino.ru."""

import re
from typing import List
import requests
from bs4 import BeautifulSoup


URL_ROOT = 'https://akvilon-mitino.ru/flat/'
URL_FLAT_PLANS = 'https://akvilon-mitino.ru/flat/?group=yes'


def get_page():
    request = requests.get('https://akvilon-mitino.ru/flat/?group=yes')
    # request = requests.get('https://akvilon-mitino.ru/flat/16432/')
    print(request.status_code)

    with open('all_grouped_flats.html', mode='wb') as writable_file:
        writable_file.write(request.content)


def find_script_tags(url: str) -> List:
    """Find and return all script tags from specified page."""
    with open('all_grouped_flats.html', mode='r') as readable_file:
        html = readable_file.read()

    # request = requests.get(url)
    # html = request.content
    # print(request.status_code)

    soup = BeautifulSoup(html, 'html.parser')

    return soup.find_all('script')


def get_flat_ids() -> List[str]:
    """Retrieve flat ids from content of script tags.

    Tags with planList in their content have information about flat ids for specific flat plan.
    This way of retrieving information helps to avoid extra requests.
    """
    script_tags = find_script_tags(URL_FLAT_PLANS)

    flat_plans = (
        script.string for script in script_tags
        if (script.string and 'planList' in script.string)
    )
    flat_ids = []
    for script in flat_plans:
        plan_flat_ids = re.findall('(\d{5})', script)
        # First value is plan_id
        flat_ids.extend(plan_flat_ids[1:])

    return flat_ids


if __name__ == '__main__':
    # get_page()
    get_flat_ids()
