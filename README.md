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



### **Build Commands**

```bash
# Full automated build
./build.sh

# Manual steps
python3 build_static_site.py  # Generate HTML
```

### **Generated Output**
- `generated/index.html` - Main overview page
- `generated/day/YYYY-MM-DD.html` - Daily event pages
- Complete with structured data, maps, and SEO optimization

## 🤖 **Automation**

### **GitHub Actions**
- **Builds and deploys** on pushes to `main` and manual workflow dispatch
- **Auto-deployment** to GitHub Pages
- **Data updates** are committed back to the repository when generated files change

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

