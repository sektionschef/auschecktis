# AusCheckt Is

find it here [https://auschecktis.at/](https://auschecktis.at/)

# Tasks
* remove the calendar logic from prompt.md and make the json format easier (withount extendedprops)

# Icons

https://www.svgrepo.com/svg/479849/wine-opener-1 

# Spezialfälle

Stöger

```
"stoeger": {
    "label": "Stöger",
    "website": "http://www.stammersdorf.com/index.php/heurige/profil/49",
    "link_opening_hours_page": "",
    "comment": "1.5.-30.8. - im Kalender, aber kenne ich nicht",
    "location": "https://maps.app.goo.gl/6St9UPESJW3xWXnU7"
}
```

Der Weingarten - keine Regelung für 2025 - Website noch auf 2024

```
    "weingarten": {
        "label": "Der Weingarten",
        "website": "https://www.derweingarten.at/",
        "link_opening_hours_page": "https://www.derweingarten.at/",
        "comment": "",
        "location": "https://maps.app.goo.gl/mrD7zkUayFaa3BFn9"
    }
```

Szüts / Suchel - gibt es noch?`
Dreh und drink - keine Öffnungszeiten für das Jahr, nur Wochenende

```

name: Check Heurigen Pages

on:
  schedule:
    - cron: '0 8 * * 1,5'  # Every Monday & Friday at 08:00 UTC
  workflow_dispatch:  # Allows manual triggering

jobs:
  run-script:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: 3.11
      - name: Install dependencies
        run: pip install beautifulsoup4 requests
      - name: Run checker
        run: python check_heurigen_updates.py


```

# local

python3 -m http.server 8000
# GitHub Pages Test
Updated: Wed Oct 29 11:20:23 CET 2025
