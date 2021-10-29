import json
from pathlib import Path
import xml.etree.ElementTree as ET
from urllib.request import Request, urlopen
import urllib.error


def main(argv):

    ensure_eos_xml()

    for item in extract_items():
        print(item)

    return 0


def extract_items():

    tree = ET.parse('eos.xml')
    for item in tree.getroot().findall('Item'):
        i = {}
        for subitem in item:
            i[subitem.tag] = subitem.text
        yield i


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


