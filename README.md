# AusCheckt Is

find it here [https://auschecktis.at/](https://auschecktis.at/)

# Tasks

# regularly check heurigen pages for updates to opening hours
```bitte lies den prompt und folge den Anweisungen für den Zeitraum {x} bis {y} für den Heurigen {z}.```

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


## 🏗️ **Build Process**

### **Files Structure**
```
├── data/                    # Individual heurigen JSON files
├── input/
│   └── heurigen_list.json  # Master list with coordinates
├── generated/              # Built static site (output)
├── build_static_site.py    # Main site generator
├── build.sh               # Automated build script
└── check_heurigen_updates.py # Data scraper
```

### **Build Commands**

```bash
# Full automated build
./build.sh

# Manual steps
python3 build_static_site.py  # Generate HTML
python3 check_heurigen_updates.py  # Update data
```

### **Generated Output**
- `generated/index.html` - Main overview page
- `generated/day/YYYY-MM-DD.html` - Daily event pages
- Complete with structured data, maps, and SEO optimization

## 🤖 **Automation**

### **GitHub Actions**
- **Daily builds** at 6 AM to fetch latest heurigen data
- **Auto-deployment** to GitHub Pages
- **Data updates** committed back to repository

### **Local Development**
```bash
# Build and serve locally
./build.sh
cd generated && python3 -m http.server 8000
```

## 🎯 **Search Engine Features**

### **JSON-LD Structured Data**
Each event includes complete Schema.org markup:
```json
{
  "@context": "https://schema.org",
  "@type": "Event", 
  "name": "Presshaus - Ausg'steckt",
  "startDate": "2025-10-31T15:00:00",
  "location": {
    "@type": "Place",
    "geo": {
      "@type": "GeoCoordinates",
      "latitude": 48.303258,
      "longitude": 16.410771
    }
  }
}
```

### **Microdata in HTML**
```html
<div itemscope itemtype="https://schema.org/Event">
  <h4 itemprop="name">Presshaus</h4>
  <time itemprop="startDate" datetime="2025-10-31T15:00:00">
    ab 15:00 Uhr
  </time>
</div>
```

