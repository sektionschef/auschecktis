# AusCheckt Is

still in beta.

# tasks
* update script with GitHub Actions - chatgpt - 


image: https://schnappen.at/oesterreich/images/stories/Bildergalerie/Heuriger/Heurigenbuschen.JPG 
ausgsteckt image. https://www.karl-lentner.com/uploads/5/8/2/9/58296093/published/ausgsteckt-april.jpg?1746690807 

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

