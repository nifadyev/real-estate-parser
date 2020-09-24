"""Parser for akvilon-mitino.ru."""

import re
from typing import List
import requests
from bs4 import BeautifulSoup


URL_ROOT = 'https://akvilon-mitino.ru'
# URL_ROOT = 'https://akvilon-mitino.ru/flat/'
URL_FLAT_PLANS = 'https://akvilon-mitino.ru/flat/?group=yes'

OUTPUT = {
    'complex': 'Аквилон Митино (Москва)',
    'type': 'flat',
    'phase': '1' or None,
    'building': '1' or '2' or '3',
    'section': '0',
    'price_base': '0',
    'price_finished': '0',
    'price_sale': '0',
    'price_finished_sale': '0',
    'area': '0',
    'living_area': '0',
    'number': '0',
    'number_on_site': '0',
    'rooms': '0',
    'floor': '0',
    'in_sale': '0',
    'sale_status': '0',
    'finished': 'optional',
    'currency': '0',
    'ceil': '0',
    'article': '0',
    'finishing_name': '0',
    'furniture': '0',
    'furniture_price': '0',
    'plan': '0',
    'feature': '0',
    'view': '0',
    'euro_planning': '0',
    'sale': '0',
    'discount_percent': '0',
    'discount': '0',
    'comment': '0',
}

FLAT_TYPES = {
    'Тип: XS': 'studio',
    'Тип: 1к': 1,
    'Тип: 2к': 2,
    'Тип: S': 2,
    'Тип: M': 3,
    'Тип: L': 4,
}


ERROR_MESSAGES = {
    'flat__type-flat': 'Flat name',
    'flat__cost-old': 'Price without discount',
    'flat__cost-new': 'Price with discount',
    'flat__info-item-value': 'Information about Area, Number, Building and Floor',
    'flat__img-file': 'Plan image',
    'flat__type-plan': 'Flat type',
    'button button--green flat__els-btn': 'Button `Забронировать`',
}



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


def parse_flat(flat=None):
    with open('flat_example.html', mode='r') as readable_file:
        html = readable_file.read()

    soup = BeautifulSoup(html, 'html.parser')

    # TODO: Use structure from make_fetcher (create dict and place values directly to it)
    flat_name = find_tag_by_class(soup, 'flat__type-flat').string
    OUTPUT['price_finished'] = format_price(raw_price=find_tag_by_class(soup, 'flat__cost-old').string)
    OUTPUT['price_finished_sale'] = format_price(raw_price=find_tag_by_class(soup, 'flat__cost-new').string)

    # Values are Area, Number, Building and Floor respectively
    flat_info = find_tags_by_class(soup, 'flat__info-item-value')
    OUTPUT['area'] = float(flat_info[0].string.replace(' м²', ''))
    OUTPUT['number'] = flat_info[1].string
    OUTPUT['building'] = flat_info[2].string
    OUTPUT['floor'] = int(flat_info[3].string)

    img_path = find_tag_by_class(soup, 'flat__img-file').attrs['src']
    OUTPUT['plan'] = f'{URL_ROOT}{img_path}'

    flat_type = find_tag_by_class(soup, 'flat__type-plan').string
    OUTPUT['rooms'] = FLAT_TYPES.get(flat_type)

    OUTPUT['euro_planning'] = int('евро' in flat_name)

    OUTPUT['in_sale'] = int(
        find_tag_by_class(soup, 'button button--green flat__els-btn').string == 'Забронировать'
    )


def format_price(raw_price):
    formatted_price = raw_price.replace(' ', '').replace('₽', '')

    return float(formatted_price)


def find_tag_by_class(soup, tag_class):
    tag = soup.find(class_=tag_class)

    if tag is None:
        raise ValueError(f'Invalid data format. {ERROR_MESSAGES.get(tag_class)} is missing.')

    return tag


def find_tags_by_class(soup, tag_class):
    tags = soup.find_all(class_=tag_class)

    if not tags:
        raise ValueError(f'Invalid data format. {ERROR_MESSAGES.get(tag_class)} is missing.')

    return tags


def validate():
    pass


if __name__ == '__main__':
    parse_flat()
    import pprint
    pprint.pprint(OUTPUT)
