import xml.etree.ElementTree as ET
from typing import Dict, List


def text_of(node: ET.Element, tag: str) -> str:
    child = node.find(tag)
    if child is None or child.text is None:
        return ""
    return child.text.strip()


def parse_feed_items(payload: bytes) -> List[Dict[str, str]]:
    try:
        root = ET.fromstring(payload)
    except ET.ParseError:
        return []

    rss_items = []
    for item in root.findall(".//item"):
        rss_items.append(
            {
                "guid": text_of(item, "guid"),
                "title": text_of(item, "title"),
                "url": text_of(item, "link"),
                "date": text_of(item, "pubDate"),
                "published_at": text_of(item, "pubDate"),
                "excerpt": text_of(item, "description"),
                "raw_category": text_of(item, "category"),
            }
        )

    if rss_items:
        return rss_items

    atom_ns = "{http://www.w3.org/2005/Atom}"
    atom_items = []
    for entry in root.findall(f".//{atom_ns}entry"):
        link = ""
        link_el = entry.find(f"{atom_ns}link")
        if link_el is not None:
            link = link_el.attrib.get("href", "")

        published = text_of(entry, f"{atom_ns}published") or text_of(
            entry, f"{atom_ns}updated"
        )
        atom_items.append(
            {
                "guid": text_of(entry, f"{atom_ns}id") or link,
                "title": text_of(entry, f"{atom_ns}title"),
                "url": link,
                "date": published,
                "published_at": published,
                "excerpt": text_of(entry, f"{atom_ns}summary")
                or text_of(entry, f"{atom_ns}content"),
                "raw_category": "",
            }
        )

    return atom_items
