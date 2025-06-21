# AusCheckt Is

still in beta.

# tasks
* update marillengartl foto und ab 12 Uhr
* maps link
* footer unten schmal
* update script with GitHub Actions - chatgpt - 


image: https://schnappen.at/oesterreich/images/stories/Bildergalerie/Heuriger/Heurigenbuschen.JPG 
ausgsteckt image. https://www.karl-lentner.com/uploads/5/8/2/9/58296093/published/ausgsteckt-april.jpg?1746690807 


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
python -m http.server 8000

