# 🍷 Auscheckt Is - SEO-Optimized Static Site

## 🎯 **New Architecture: Static Site Generator**

This project has been redesigned from a JavaScript-heavy FullCalendar.js app to a **SEO-optimized static site generator** that creates search engine-friendly HTML pages with structured data.

## ✨ **Features**

### 🔍 **SEO Optimized**
- **JSON-LD structured data** for every event (Schema.org Event markup)
- **Static HTML** pages that search engines can crawl
- **Meta tags** optimized for each day's events
- **Microdata** embedded in HTML for rich snippets

### 🗺️ **Interactive Maps** 
- **Leaflet maps** with custom markers for each location
- **Progressive enhancement** - works without JavaScript
- **Coordinates stored** in master heurigen_list.json

### 📱 **Performance**
- **Fast loading** static HTML pages
- **Mobile-first** responsive design
- **Minimal JavaScript** (only for maps)
- **Better Core Web Vitals** scores

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

## 📊 **SEO Benefits**

### **Before (JavaScript Calendar)**
- ❌ Search engines couldn't index events
- ❌ No structured data
- ❌ Slow loading with heavy JS

### **After (Static Site)**
- ✅ **Every event** indexed by search engines
- ✅ **Rich snippets** in search results 
- ✅ **Local SEO** optimized for "Heuriger Wien heute"
- ✅ **Fast loading** static pages
- ✅ **Mobile-friendly** indexing

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

## 🚀 **Deployment**

### **GitHub Pages (Automatic)**
- Pushes to `main` trigger automated builds
- Deploys to `your-username.github.io/auschecktis`
- Daily updates at 6 AM

### **Custom Server**
```bash
rsync -av generated/ user@server:/var/www/html/
```

## 📈 **Expected SEO Impact**

- **Local search visibility** for "Heuriger Stammersdorf"
- **Event rich snippets** in Google search
- **Better mobile indexing** scores
- **Faster page load** times
- **Improved user experience** metrics

## 🔧 **Technical Stack**

- **Python 3** - Static site generator
- **Leaflet.js** - Interactive maps
- **Bootstrap 5** - Responsive design
- **Schema.org** - Structured data
- **GitHub Actions** - CI/CD automation

---

*This rewrite transforms the site from a JavaScript app to a search engine-friendly static site while preserving all interactive features users love.*