import logging
import json
from pathlib import Path
from urllib.request import Request, urlopen
import urllib.error
import xml.etree.ElementTree as ET


LOGGER = logging.getLogger(__name__)


def main(argv):

    logging.basicConfig(level=logging.DEBUG)

    ensure_eos_xml()

    for item in extract_items():
        LOGGER.info('item: %r', item)

    return 0


def extract_items():

    tree = ET.parse('eos.xml')

    headings = {}
    product = None
    for i, item in enumerate(tree.getroot().findall('Item')):

        # Special handling for first Item, it gives us the descriptions of
        # subsequent headings
        if i == 0:

            for subitem in item:
                headings[subitem.tag] = subitem.text.split('\n')[0]
            LOGGER.debug('headings: %r', headings)

        else:
            id_ = item.find('ID')
            if not (id_ is None):

                LOGGER.debug('begin product %r', id_.text)

                if not (product is None):
                    LOGGER.debug('finalize product: %r', product)
                    yield product

                product = {}
                for subitem in item:
                    product[subitem.tag] = subitem.text
                product['table'] = []

            else:

                row = {}
                for subitem in item:
                    row[subitem.tag] = subitem.text
                LOGGER.debug('row: %r', row)
                product['table'].append(row)

    LOGGER.debug('final product: %r', product)
    yield product


def ensure_eos_xml():

    eos_path = Path('eos.xml')
    headers_path = Path('eos.xml-headers.json')

    r = Request('https://techlibrary.hpe.com/data/xml/eos/eos.xml')

    if headers_path.exists():
        with open(headers_path, 'r') as f:
            try:
                old_headers = json.load(f)
            except Exception as e:
                pass
            else:
                if 'Last-Modified' in old_headers:
                    r.add_header('If-Modified-Since', old_headers['Last-Modified'])

    try:
        with urlopen(r) as u:
            if u.status == 304:
                assert eos_path.exists()
                return

            with open(eos_path, 'wb') as f:
                f.write(u.read())

            with open(headers_path, 'w') as f:
                json.dump(dict(u.headers.items()), f)

    except urllib.error.HTTPError as e:
        if e.code == 304:
            if not eos_path.exists():
                headers_path.unlink()
                ensure_eos_xml()
        else:
            raise


