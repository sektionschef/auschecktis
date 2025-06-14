
* Almdudler Standl
* Presshau
* Wieninger
* Bartholomäus 
* Krenek
* Biohof 5
* Lentner karl

# tasks
* mastereinheit
* goat counter id
* script übersiedeln
* update script with GitHub Actions - chatgpt - 

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




🛠️ Implementation Plan
1. Set up GitHub Pages
Create a GitHub repository (e.g., stammersdorf-heurigen-calendar)

Enable GitHub Pages in the settings (from the main branch or /docs folder)

2. HTML Template
I’ll create a single-page Bootstrap template that includes:

A FullCalendar.js widget

Placeholder for heurigen events

Mobile-friendly layout

Header section with a short description

3. Event Source
You can:

Start with a static .json file listing the heurigen opening hours (easy to update manually or script with AI help)

Later automate updates from heurigen websites

4. Analytics Integration
Add a snippet from Plausible or GoatCounter

These work with GitHub Pages and are GDPR-friendly