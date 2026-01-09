import requests
import gzip
import xml.etree.ElementTree as ET
from io import BytesIO
from flask import Flask, send_file
import threading
import time
from datetime import datetime

# -----------------------------
# CONFIG: Feeds to merge
# -----------------------------
EPG_FEEDS = [
    "https://epgshare01.online/epgshare01/epg_ripper_US2.xml.gz",
    "https://epgshare01.online/epgshare01/epg_ripper_US_LOCALS1.xml.gz",
    "https://epgshare01.online/epgshare01/epg_ripper_US_SPORTS1.xml.gz",
    "https://epgshare01.online/epgshare01/epg_ripper_CA2.xml.gz",
    "https://epgshare01.online/epgshare01/epg_ripper_PLEX1.xml.gz"
]

LOCAL_FILE = "merged_epg.xml.gz"
UPDATE_INTERVAL_HOURS = 24  # daily

app = Flask(__name__)

# -----------------------------
# Function: Merge all feeds
# -----------------------------
def update_epg():
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
                print(f"[{datetime.now()}] Success")
            except Exception as e:
                print(f"[{datetime.now()}] Failed to download {url}: {e}")

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
        print(f"[{datetime.now()}] Next update in {UPDATE_INTERVAL_HOURS} hours...\n")
        time.sleep(UPDATE_INTERVAL_HOURS * 3600)

# -----------------------------
# Flask routes
# -----------------------------
@app.route("/")
def index():
    return f"<h2>EPG Server</h2><p>Download merged EPG: <a href='/merged_epg.xml.gz'>merged_epg.xml.gz</a></p>"

@app.route("/merged_epg.xml.gz")
def serve_epg():
    try:
        return send_file(LOCAL_FILE, mimetype="application/gzip", as_attachment=True)
    except Exception as e:
        return f"EPG file not available yet: {e}", 404

# -----------------------------
# Start everything
# -----------------------------
if __name__ == "__main__":
    threading.Thread(target=update_epg, daemon=True).start()
    port = int(os.environ.get("PORT", 8000))
    app.run(host="0.0.0.0", port=port)
