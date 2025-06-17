

# tasks
* script übersiedeln
* update script with GitHub Actions - chatgpt - 
* impressum - link github
* intro satz - was ist dass


font: https://fonts.google.com/specimen/UnifrakturMaguntia?preview.text=AusCheckt%20is 
image: https://schnappen.at/oesterreich/images/stories/Bildergalerie/Heuriger/Heurigenbuschen.JPG 


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

