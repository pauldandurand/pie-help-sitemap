
# generate_helpcenter_sitemap.py
# Fetches all public Zendesk Help Center articles and builds sitemap.xml.
# Usage (from this folder): python3 generate_helpcenter_sitemap.py

import json, sys, urllib.request, urllib.error
from datetime import datetime, timezone
import xml.etree.ElementTree as ET

BASE = "https://help.pie.me"       # change if your help center subdomain changes
LOCALE = "en-us"                    # change if using a different default locale
PER_PAGE = 100                      # Zendesk API supports up to 100
OUTPUT = "help-center-sitemap.xml"  # output file name

def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": "pie-sitemap-generator/1.0"})
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read().decode("utf-8"))

def iso_date(s):
    # Zendesk uses ISO timestamps. Normalize to YYYY-MM-DD.
    # Fallback to today's date if missing.
    if not s:
        return datetime.now(timezone.utc).date().isoformat()
    try:
        # e.g. "2025-06-29T11:32:51Z"
        return datetime.fromisoformat(s.replace("Z","+00:00")).date().isoformat()
    except Exception:
        return datetime.now(timezone.utc).date().isoformat()

def main():
    start = f"{BASE}/api/v2/help_center/{LOCALE}/articles.json?per_page={PER_PAGE}"
    urls = []
    seen = set()
    next_url = start
    while next_url:
        data = fetch(next_url)
        for a in data.get("articles", []):
            u = a.get("html_url")
            if u and u not in seen:
                seen.add(u)
                urls.append((u, iso_date(a.get("updated_at"))))
        next_url = data.get("next_page")

    # Build sitemap
    urlset = ET.Element("urlset", xmlns="http://www.sitemaps.org/schemas/sitemap/0.9")
    for u, lastmod in sorted(urls, key=lambda x: x[0]):
        url_el = ET.SubElement(urlset, "url")
        loc = ET.SubElement(url_el, "loc"); loc.text = u
        lm = ET.SubElement(url_el, "lastmod"); lm.text = lastmod
        cf = ET.SubElement(url_el, "changefreq"); cf.text = "weekly"
        pr = ET.SubElement(url_el, "priority"); pr.text = "0.6"

    tree = ET.ElementTree(urlset)
    tree.write(OUTPUT, encoding="utf-8", xml_declaration=True)
    print(f"Wrote {OUTPUT} with {len(urls)} URLs.")

if __name__ == "__main__":
    main()
