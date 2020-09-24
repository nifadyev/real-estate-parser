"""Parser for akvilon-mitino.ru."""

import re
from typing import List, Dict, Any
import requests
from bs4 import BeautifulSoup
from bs4.element import ResultSet, Tag


URL_ROOT = 'https://akvilon-mitino.ru'


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


def parse() -> List[Dict[str, Any]]:
    """Parse available properties on partner's site.

    Returns:
        list: sequence of JSON representations of all partner properties.
    """
    flat_ids = get_flat_ids()

    return [parse_flat(flat_id) for flat_id in flat_ids]


def get_flat_ids() -> List[str]:
    """Retrieve flat ids from content of script tags.

    Tags with planList in their content have information about flat ids for specific flat plan.
    This way of retrieving information helps to avoid extra requests.

    Returns:
        list: sequence of unique flat identifiers of partner's site.
    """
    script_tags = find_script_tags(url='https://akvilon-mitino.ru/flat/?group=yes')

    flat_plans = (
        script.string for script in script_tags
        if (script.string and 'planList' in script.string)
    )
    flat_ids = []
    for script in flat_plans:
        plan_flat_ids = re.findall(r'(\d{5})', script)
        # First value is plan_id, not flat_id
        flat_ids.extend(plan_flat_ids[1:])

    return flat_ids


def find_script_tags(url: str) -> ResultSet:
    """Find all script tags in HTML response.

    Args:
        url: path to page with flat plans.

    Raises:
        ValueError: request is not succeed.
        ValueError: script tags are not found in HTML response.

    Returns:
        ResultSet: sequence of script tags with attributes and content.
    """
    request = requests.get(url)
    if request.status_code != 200:
        raise ValueError('Request to get flat plans failed.')

    soup = BeautifulSoup(markup=request.content, features='html.parser')

    tags = soup.find_all('script')
    if not tags:
        raise ValueError('Invalid data format. Script tags are not found.')

    return tags


def parse_flat(flat_id) -> Dict[str, Any]:
    """Make request to partner's site and parse response.

    Args:
        flat_id: unique flat identifier.

    Raises:
        ValueError: request is not succeed.

    Returns:
        dict: JSON flat representation.

    """
    request = requests.get(f'{URL_ROOT}/flat/{flat_id}/')
    if request.status_code != 200:
        raise ValueError(f'Request with flat_id {flat_id} failed.')

    soup = BeautifulSoup(markup=request.content, features='html.parser')
    flat_name = find_tag_by_class(soup, 'flat__type-flat').string
    img_path = find_tag_by_class(soup, 'flat__img-file').attrs['src']
    flat_type = find_tag_by_class(soup, 'flat__type-plan').string
    is_bookable = find_tag_by_class(soup, 'button button--green flat__els-btn').string == 'Забронировать'
    # Values are Area, Number, Building and Floor respectively
    flat_info = find_tags_by_class(soup, 'flat__info-item-value')

    return {
        'complex': 'Аквилон Митино (Москва)',
        'type': 'flat',
        'phase': None,
        'building': flat_info[2].string,
        'section': None,
        'price_base': None,
        'price_finished': format_price(raw_price=find_tag_by_class(soup, 'flat__cost-old').string),
        'price_sale': None,
        'price_finished_sale': format_price(raw_price=find_tag_by_class(soup, 'flat__cost-new').string),
        'area': float(flat_info[0].string.replace(' м²', '')),
        'living_area': None,
        'number': flat_info[1].string,
        'number_on_site': None,
        'rooms': FLAT_TYPES.get(flat_type),
        'floor': int(flat_info[3].string),
        'in_sale': int(is_bookable),
        'sale_status': None,
        'finished': 1,
        'currency': None,
        'ceil': None,
        'article': None,
        'finishing_name': 'Предчистовая',
        'furniture': None,
        'furniture_price': None,
        'plan': f'{URL_ROOT}{img_path}',
        'feature': None,
        'view': None,
        'euro_planning': int('евро' in flat_name),
        'sale': None,
        'discount_percent': None,
        'discount': None,
    }


def find_tag_by_class(soup: BeautifulSoup, tag_class: str) -> Tag:
    """Find and return tag in HTML response or raise an error.

    Args:
        soup: BeautifulSoup instance.
        tag_class: class of searched HTML element.

    Raises:
        ValueError: tag is not found in HTML response.

    Returns:
        Tag: Tag instance.
    """
    tag = soup.find(class_=tag_class)

    if tag is None:
        raise ValueError(f'Invalid data format. {ERROR_MESSAGES.get(tag_class)} is not found.')

    return tag


def find_tags_by_class(soup: BeautifulSoup, tag_class: str) -> ResultSet:
    """Find and return tags sequence in HTML response or raise an error.

    Args:
        soup: BeautifulSoup instance.
        tag_class: class of searched HTML element.

    Raises:
        ValueError: tags are not found in HTML response.

    Returns:
        ResultSet: sequence of tags with attributes and content.
    """
    tags = soup.find_all(class_=tag_class)

    if not tags:
        raise ValueError(f'Invalid data format. {ERROR_MESSAGES.get(tag_class)} is not found.')

    return tags


def format_price(raw_price: str) -> float:
    """Remove extra chars and convert price to float."""
    formatted_price = raw_price.replace(' ', '').replace('₽', '')

    return float(formatted_price)


if __name__ == '__main__':
    result = parse()
