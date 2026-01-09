import requests
import gzip
import xml.etree.ElementTree as ET
from io import BytesIO
from flask import Flask, send_file
import os

EPG_FEEDS = [
    "https://epgshare01.online/epgshare01/epg_ripper_US2.xml.gz",
    "https://epgshare01.online/epgshare01/epg_ripper_US_LOCALS1.xml.gz",
    "https://epgshare01.online/epgshare01/epg_ripper_US_SPORTS1.xml.gz",
    "https://epgshare01.online/epgshare01/epg_ripper_CA2.xml.gz",
    "https://epgshare01.online/epgshare01/epg_ripper_PLEX1.xml.gz"
]

LOCAL_FILE = "merged_epg.xml.gz"

def merge_feeds():
    feeds = []
    for url in EPG_FEEDS:
        try:
            print(f"Downloading {url} ...")
            r = requests.get(url)
            r.raise_for_status()
            with gzip.open(BytesIO(r.content), "rb") as f:
                tree = ET.parse(f)
                feeds.append(tree)
            print(f"Downloaded {url}")
        except Exception as e:
            print(f"Failed {url}: {e}")

    merged_root = ET.Element("tv")
    for tree in feeds:
        for elem in tree.getroot():
            merged_root.append(elem)

    merged_tree = ET.ElementTree(merged_root)
    merged_bytes = BytesIO()
    merged_tree.write(merged_bytes, encoding="utf-8", xml_declaration=True)

    with gzip.open(LOCAL_FILE, "wb") as f:
        f.write(merged_bytes.getvalue())
    print(f"Merged EPG saved as {LOCAL_FILE}")

# Merge feeds **once on startup**
merge_feeds()

# Flask server
app = Flask(__name__)

@app.route("/")
def serve_epg():
    return send_file(LOCAL_FILE, mimetype="application/gzip")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
