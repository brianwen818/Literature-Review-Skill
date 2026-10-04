"""Zotero Web API: read what a library already holds, add items, export RDF.

Only bibliographic records are written; no files are uploaded."""
import re
import time
import uuid
import xml.etree.ElementTree as ET

import requests

from .textutil import normalize_doi, normalize_title

API = "https://api.zotero.org"
UPLOAD_BATCH = 50
ID_PREFIX = "lit-review-id:"

ITEM_TYPE = {
    "journal-article": "journalArticle", "book": "book", "monograph": "book", "edited-book": "book",
    "reference-book": "book", "book-chapter": "bookSection", "book-section": "bookSection",
    "book-part": "bookSection", "posted-content": "preprint", "dissertation": "thesis",
    "report": "report", "proceedings-article": "conferencePaper", "unknown": "document",
}


class ZoteroError(RuntimeError):
    pass


def settings_from_env(env):
    """Accepts the keys in templates/zotero-info/.env.example (and the older ZOTERO_GROUP_ID)."""
    library_id = env.get("ZOTERO_LIBRARY_ID") or env.get("ZOTERO_GROUP_ID") or ""
    library_type = (env.get("ZOTERO_LIBRARY_TYPE") or ("group" if env.get("ZOTERO_GROUP_ID") else "")).lower()
    missing = [name for name, value in (("ZOTERO_API_KEY", env.get("ZOTERO_API_KEY")),
                                         ("ZOTERO_LIBRARY_ID", library_id),
                                         ("ZOTERO_LIBRARY_TYPE", library_type)) if not value]
    if missing:
        raise ZoteroError("missing in zotero-info/.env: " + ", ".join(missing))
    if library_type not in ("group", "user"):
        raise ZoteroError("ZOTERO_LIBRARY_TYPE must be 'group' or 'user'")
    return {"api_key": env["ZOTERO_API_KEY"], "library_type": library_type, "library_id": library_id}


class Zotero:
    def __init__(self, api_key, library_type, library_id):
        self.library_type, self.library_id = library_type, str(library_id)
        self.base = f"{API}/{'groups' if library_type == 'group' else 'users'}/{library_id}"
        self.session = requests.Session()
        self.session.headers.update({"Zotero-API-Key": api_key, "Zotero-API-Version": "3"})
        self._templates = {}

    def _request(self, method, url, **kwargs):
        for attempt in range(6):
            response = self.session.request(method, url, timeout=60, **kwargs)
            wait = response.headers.get("Backoff") or (
                response.headers.get("Retry-After") if response.status_code in (429, 503) else None)
            if response.status_code in (429, 503) and attempt < 5:
                time.sleep(min(float(wait or 5), 60))
                continue
            if wait:
                time.sleep(min(float(wait), 60))
            return response
        return response

    def can_write(self):
        """(library access, write access) of the API key for this library."""
        response = self._request("GET", f"{API}/keys/current")
        if response.status_code != 200:
            raise ZoteroError(f"API key rejected (HTTP {response.status_code})")
        access = response.json().get("access", {})
        if self.library_type == "user":
            rights = access.get("user", {})
        else:
            groups = access.get("groups", {})
            rights = groups.get(self.library_id) or groups.get("all") or {}
        return bool(rights.get("library")), bool(rights.get("write"))

    def iter_items(self, **params):
        """Top-level items only (child attachments and notes are skipped)."""
        start = 0
        while True:
            response = self._request("GET", f"{self.base}/items/top",
                                     params={"limit": 100, "start": start, **params})
            if response.status_code != 200:
                raise ZoteroError(f"reading items failed (HTTP {response.status_code}): {response.text[:200]}")
            batch = response.json()
            for item in batch:
                yield item
            if len(batch) < 100:
                return
            start += 100

    def existing(self):
        """What the library already holds, each mapped to its item key:
        DOIs, normalised titles, and the lit-review ids written by earlier
        runs (which make re-runs idempotent)."""
        dois, titles, ids = {}, {}, {}
        for item in self.iter_items():
            data = item.get("data", {})
            extra = data.get("extra", "") or ""
            in_extra = re.search(r"^DOI:\s*(\S+)", extra, re.M | re.I)
            doi = normalize_doi(data.get("DOI")) or normalize_doi(in_extra.group(1) if in_extra else "")
            if doi:
                dois[doi] = item["key"]
            title = normalize_title(data.get("title"))
            if title:
                titles[title] = item["key"]
            match = re.search(rf"^{ID_PREFIX}\s*(\S+)", extra, re.M)
            if match:
                ids[match.group(1)] = item["key"]
        return dois, titles, ids

    def collections(self):
        found, start = [], 0
        while True:
            response = self._request("GET", f"{self.base}/collections", params={"limit": 100, "start": start})
            if response.status_code != 200:
                raise ZoteroError(f"reading collections failed (HTTP {response.status_code})")
            batch = response.json()
            found.extend(batch)
            if len(batch) < 100:
                return found
            start += 100

    def ensure_collection(self, spec):
        """spec: a collection key, or a name / 'Parent/Child' path (created if absent)."""
        if not spec:
            return ""
        existing = self.collections()
        if any(c["key"] == spec for c in existing):
            return spec
        parent = False
        for name in [part.strip() for part in spec.split("/") if part.strip()]:
            match = next((c for c in existing if c["data"]["name"] == name
                          and (c["data"].get("parentCollection") or False) == parent), None)
            if match:
                parent = match["key"]
                continue
            response = self._request("POST", f"{self.base}/collections",
                                     json=[{"name": name, "parentCollection": parent}],
                                     headers={"Zotero-Write-Token": uuid.uuid4().hex})
            result = response.json() if response.status_code == 200 else {}
            if not result.get("successful"):
                raise ZoteroError(f"could not create collection '{name}': {response.text[:200]}")
            created = result["successful"]["0"]
            existing.append(created)
            parent = created["key"]
        return parent

    def template(self, item_type):
        if item_type not in self._templates:
            response = self._request("GET", f"{API}/items/new", params={"itemType": item_type})
            if response.status_code != 200:
                raise ZoteroError(f"no template for item type {item_type}")
            self._templates[item_type] = response.json()
        return dict(self._templates[item_type])

    def build_item(self, record, item_id, collection, tags, extra_lines=()):
        """Bibliographic record -> Zotero item, using only fields the item type has
        (unknown fields make the API reject the whole item)."""
        item_type = ITEM_TYPE.get(record.get("type", ""), "journalArticle")
        item = self.template(item_type)
        creators = []
        for role, people in (("author", record.get("authors", [])), ("editor", record.get("editors", []))):
            for person in people:
                if person.get("family"):
                    creators.append({"creatorType": role, "lastName": person["family"],
                                     "firstName": person.get("given", "")})
                elif person.get("name"):
                    creators.append({"creatorType": role, "name": person["name"]})
        if not creators and record.get("authors_str"):
            creators.append({"creatorType": "author", "name": record["authors_str"]})
        extra = [f"{ID_PREFIX} {item_id}", *extra_lines]
        values = {
            "title": record.get("title", ""), "abstractNote": record.get("abstract", ""),
            "date": record.get("year", ""), "volume": record.get("volume", ""),
            "issue": record.get("issue", ""), "pages": record.get("pages", ""),
            "publisher": record.get("publisher", "") if item_type != "journalArticle" else "",
            "url": record.get("url", ""), "DOI": record.get("doi", ""),
            "ISSN": ", ".join(record.get("issns", [])[:2]),
        }
        container_field = {"journalArticle": "publicationTitle", "bookSection": "bookTitle",
                           "conferencePaper": "proceedingsTitle"}.get(item_type)
        if container_field:
            values[container_field] = record.get("journal", "")
        for field, value in values.items():
            if field in item and value:
                item[field] = str(value)
        if record.get("doi") and "DOI" not in item:
            extra.insert(0, f"DOI: {record['doi']}")
        item["creators"] = creators
        item["tags"] = [{"tag": tag} for tag in tags]
        item["collections"] = [collection] if collection else []
        item["extra"] = "\n".join(extra)
        return item

    def create_items(self, items):
        """POST in batches. Returns ({index: key}, {index: error message})."""
        created, failed = {}, {}
        for start in range(0, len(items), UPLOAD_BATCH):
            batch = items[start:start + UPLOAD_BATCH]
            response = self._request("POST", f"{self.base}/items", json=batch,
                                     headers={"Zotero-Write-Token": uuid.uuid4().hex})
            if response.status_code != 200:
                for offset in range(len(batch)):
                    failed[start + offset] = f"HTTP {response.status_code}: {response.text[:150]}"
                continue
            result = response.json()
            for index, item in result.get("successful", {}).items():
                created[start + int(index)] = item["key"]
            for index, error in result.get("failed", {}).items():
                failed[start + int(index)] = f"{error.get('code')}: {error.get('message')}"
        return created, failed

    def export_rdf(self, keys):
        """Zotero RDF for the given item keys, merged into one document."""
        documents = []
        for start in range(0, len(keys), UPLOAD_BATCH):
            response = self._request("GET", f"{self.base}/items", params={
                "itemKey": ",".join(keys[start:start + UPLOAD_BATCH]),
                "format": "rdf_zotero", "limit": UPLOAD_BATCH})
            if response.status_code != 200:
                raise ZoteroError(f"RDF export failed (HTTP {response.status_code})")
            documents.append(response.content.decode("utf-8"))
        return merge_rdf(documents)


def merge_rdf(documents):
    """Join several rdf:RDF documents by moving their children under one root."""
    if not documents:
        return ""
    for document in documents:
        for prefix, uri in re.findall(r'xmlns:([\w\-]+)="([^"]+)"', document[:5000]):
            ET.register_namespace(prefix, uri)
    root = ET.fromstring(documents[0].encode("utf-8"))
    for document in documents[1:]:
        root.extend(list(ET.fromstring(document.encode("utf-8"))))
    return ET.tostring(root, encoding="unicode", xml_declaration=True)
