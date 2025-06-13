import requests
from bs4 import BeautifulSoup
from hashlib import md5
import os

# URLs to monitor
URLS = {
    "Biohof Steindl": "https://biohof-steindl.at/?p=1281",
    "Bartholomäus Hütte": "https://bartholomaeushuette.wordpress.com/",
}

# File to store last known hashes
HASH_FILE = "heurigen_hashes.txt"


def load_hashes():
    if not os.path.exists(HASH_FILE):
        return {}
    with open(HASH_FILE, "r") as f:
        return dict(line.strip().split("|", 1) for line in f if "|" in line)


def save_hashes(hashes):
    with open(HASH_FILE, "w") as f:
        for name, hash_val in hashes.items():
            f.write(f"{name}|{hash_val}\n")


def get_page_hash(url):
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        text = soup.get_text(strip=True)
        return md5(text.encode("utf-8")).hexdigest()
    except Exception as e:
        print(f"Error checking {url}: {e}")
        return None


def check_for_updates():
    old_hashes = load_hashes()
    new_hashes = {}
    changes = []

    for name, url in URLS.items():
        new_hash = get_page_hash(url)
        if new_hash:
            new_hashes[name] = new_hash
            if name in old_hashes and old_hashes[name] != new_hash:
                changes.append(name)
            elif name not in old_hashes:
                changes.append(name + " (first time)")

    save_hashes(new_hashes)

    if changes:
        print("Updates detected for:")
        for change in changes:
            print(f"- {change}")
    else:
        print("No updates detected.")


if __name__ == "__main__":
    check_for_updates()
