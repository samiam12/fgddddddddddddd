import os
import time
import gzip
import requests
import xml.etree.ElementTree as ET
from io import BytesIO
from datetime import datetime
from threading import Thread
from flask import Flask, send_file

# -----------------------------
# CONFIG
# -----------------------------
EPG_FEEDS = [
    "https://epgshare01.online/epgshare01/epg_ripper_US2.xml.gz",
    "https://epgshare01.online/epgshare01/epg_ripper_US_LOCALS1.xml.gz",
    "https://epgshare01.online/epgshare01/epg_ripper_US_SPORTS1.xml.gz",
    "https://epgshare01.online/epgshare01/epg_ripper_CA2.xml.gz",
    "https://epgshare01.online/epgshare01/epg_ripper_PLEX1.xml.gz"
]

LOCAL_FILE = "merged_epg.xml.gz"
UPDATE_INTERVAL_HOURS = 24  # update daily

# -----------------------------
# Flask app
# -----------------------------
app = Flask(__name__)

@app.route("/")
def home():
    return "EPG Merge Service is running!"

@app.route(f"/{LOCAL_FILE}")
def serve_epg():
    if os.path.exists(LOCAL_FILE):
        return send_file(LOCAL_FILE, mimetype="application/gzip")
    return "EPG not available yet. Try again in a few seconds.", 503

# -----------------------------
# Merge feeds
# -----------------------------
def merge_feeds():
    while True:
        print(f"[{datetime.now()}] Starting EPG update...")
        feeds = []
        for url in EPG_FEEDS:
            try:
                print(f"[{datetime.now()}] Downloading {url} ...")
                response = requests.get(url, timeout=30)
                response.raise_for_status()
                with gzip.open(BytesIO(response.content), "rb") as f:
                    tree = ET.parse(f)
                    feeds.append(tree)
                print(f"[{datetime.now()}] Successfully downloaded {url}")
            except Exception as e:
                print(f"[{datetime.now()}] Failed {url}: {e}")

        if feeds:
            merged_root = ET.Element("tv")
            for tree in feeds:
                root = tree.getroot()
                for elem in root:
                    merged_root.append(elem)
            merged_tree = ET.ElementTree(merged_root)
            merged_bytes = BytesIO()
            merged_tree.write(merged_bytes, encoding="utf-8", xml_declaration=True)

            with gzip.open(LOCAL_FILE, "wb") as f:
                f.write(merged_bytes.getvalue())

            print(f"[{datetime.now()}] Merged EPG saved as {LOCAL_FILE}")
        else:
            print(f"[{datetime.now()}] No feeds downloaded, skipping merge.")

        print(f"[{datetime.now()}] Next update in {UPDATE_INTERVAL_HOURS} hours\n")
        time.sleep(UPDATE_INTERVAL_HOURS * 3600)

# -----------------------------
# Run everything
# -----------------------------
if __name__ == "__main__":
    # Start background updater
    Thread(target=merge_feeds, daemon=True).start()

    # Start Flask server on the port Render assigns
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
