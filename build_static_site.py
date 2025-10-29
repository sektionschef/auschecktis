#!/usr/bin/env python3
"""
Static Site Generator for Auscheckt Is
Converts JSON event data to SEO-optimized static HTML with structured data
"""

import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Any
import re

class HeurigenSiteGenerator:
    def __init__(self, base_dir: str = "."):
        self.base_dir = base_dir
        self.data_dir = os.path.join(base_dir, "data")
        self.input_dir = os.path.join(base_dir, "input")
        self.output_dir = os.path.join(base_dir, "generated")
        
        # Load master heurigen data
        with open(os.path.join(self.input_dir, "heurigen_list.json"), 'r', encoding='utf-8') as f:
            self.heurigen_master = json.load(f)
    
    def load_all_events(self) -> List[Dict[str, Any]]:
        """Load all events from data/*.json files"""
        all_events = []
        
        for filename in os.listdir(self.data_dir):
            if filename.endswith('.json') and filename != 'archive':
                heurigen_key = filename.replace('.json', '')
                file_path = os.path.join(self.data_dir, filename)
                
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        events = json.load(f)
                    
                    # Add heurigen metadata to each event
                    for event in events:
                        event['heurigen_key'] = heurigen_key
                        if heurigen_key in self.heurigen_master:
                            event['heurigen_data'] = self.heurigen_master[heurigen_key]
                        all_events.append(event)
                        
                except Exception as e:
                    print(f"Error loading {filename}: {e}")
        
        # Sort events by start date
        all_events.sort(key=lambda x: x['start'])
        return all_events
    
    def generate_json_ld(self, event: Dict[str, Any]) -> str:
        """Generate JSON-LD structured data for an event"""
        heurigen_data = event.get('heurigen_data', {})
        
        json_ld = {
            "@context": "https://schema.org",
            "@type": "Event",
            "name": f"{event['title']} - Ausg'steckt",
            "description": f"Der Heurige {event['title']} hat ausg'steckt in Stammersdorf, Wien",
            "startDate": event['start'],
            "endDate": event['end'],
            "eventStatus": "https://schema.org/EventScheduled",
            "eventAttendanceMode": "https://schema.org/OfflineEventAttendanceMode",
            "location": {
                "@type": "Place",
                "name": event['title'],
                "address": {
                    "@type": "PostalAddress",
                    "addressLocality": "Wien",
                    "addressRegion": "Wien",
                    "addressCountry": "AT",
                    "postalCode": "1210"
                }
            },
            "url": event.get('url', ''),
            "organizer": {
                "@type": "Organization", 
                "name": event['title'],
                "url": event.get('url', '')
            }
        }
        
        # Add coordinates if available
        if 'extendedProps' in event:
            props = event['extendedProps']
            if 'lat' in props and 'lng' in props:
                json_ld['location']['geo'] = {
                    "@type": "GeoCoordinates",
                    "latitude": props['lat'],
                    "longitude": props['lng']
                }
        
        return json.dumps(json_ld, indent=2, ensure_ascii=False)
    
    def format_date_german(self, date_str: str) -> str:
        """Format ISO date to German format"""
        dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        weekdays = ['Montag', 'Dienstag', 'Mittwoch', 'Donnerstag', 'Freitag', 'Samstag', 'Sonntag']
        weekday = weekdays[dt.weekday()]
        return f"{weekday}, {dt.strftime('%d.%m.%Y')}"
    
    def format_time_german(self, date_str: str) -> str:
        """Format ISO time to German format"""
        dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        return dt.strftime('%H:%M')
    
    def generate_event_html(self, event: Dict[str, Any]) -> str:
        """Generate HTML for a single event with microdata"""
        heurigen_data = event.get('heurigen_data', {})
        start_time = self.format_time_german(event['start'])
        map_link = event.get('extendedProps', {}).get('mapLink', '')
        
        return f'''
        <div class="event-card mb-3 p-3 border rounded" itemscope itemtype="https://schema.org/Event">
            <h4 itemprop="name">{event['title']}</h4>
            <div class="event-details">
                <time itemprop="startDate" datetime="{event['start']}" class="text-muted">
                    ab {start_time} Uhr
                </time>
                <div itemprop="location" itemscope itemtype="https://schema.org/Place">
                    <span itemprop="name" class="d-none">{event['title']}</span>
                    <div itemprop="address" itemscope itemtype="https://schema.org/PostalAddress">
                        <span itemprop="addressLocality" class="d-none">Wien</span>
                        <span itemprop="addressRegion" class="d-none">Wien</span>
                        <span itemprop="postalCode" class="d-none">1210</span>
                    </div>
                </div>
            </div>
            <div class="event-actions mt-2">
                <a href="{event.get('url', '#')}" target="_blank" class="btn btn-sm btn-outline-primary" itemprop="url">
                    Website
                </a>
                {f'<a href="{map_link}" target="_blank" class="btn btn-sm btn-outline-secondary">Google Maps</a>' if map_link else ''}
            </div>
        </div>'''
    
    def generate_daily_page(self, date: datetime, events: List[Dict[str, Any]]) -> str:
        """Generate HTML page for a specific date"""
        date_str = date.strftime('%Y-%m-%d')
        date_german = self.format_date_german(date.isoformat())
        
        # Filter events for this date
        day_events = [e for e in events if e['start'].startswith(date_str)]
        
        # Generate JSON-LD for all events on this day
        json_ld_list = [self.generate_json_ld(event) for event in day_events]
        json_ld_combined = ',\n'.join(json_ld_list) if json_ld_list else ''
        
        # Generate event HTML
        events_html = ''
        map_markers = []
        
        if day_events:
            events_html = '\n'.join([self.generate_event_html(event) for event in day_events])
            
            # Prepare map markers
            for event in day_events:
                if 'extendedProps' in event:
                    props = event['extendedProps']
                    if 'lat' in props and 'lng' in props:
                        map_markers.append({
                            'lat': props['lat'],
                            'lng': props['lng'],
                            'title': event['title'],
                            'url': event.get('url', '#'),
                            'mapLink': props.get('mapLink', '')
                        })
        else:
            events_html = '<p class="text-muted">Kein Heuriger hat heute ausg\'steckt.</p>'
        
        # Generate map JavaScript
        map_js = self.generate_map_js(map_markers)
        
        html_template = f'''<!DOCTYPE html>
<html lang="de">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Heurigen {date_german} - Auscheckt Is</title>
    <meta name="description" content="Welche Heurigen haben am {date_german} ausg'steckt? Alle Öffnungszeiten und Standorte der Stammersdorfer Heurigen.">
    
    <!-- Favicons -->
    <link rel="icon" type="image/png" href="/favicon-96x96.png" sizes="96x96" />
    <link rel="icon" type="image/svg+xml" href="/favicon.svg" />
    <link rel="shortcut icon" href="/favicon.ico" />
    <link rel="apple-touch-icon" sizes="180x180" href="/apple-touch-icon.png" />
    <link rel="manifest" href="/site.webmanifest" />
    
    <!-- CSS -->
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
    <link rel="stylesheet" href="/custom.css">
    
    <!-- Structured Data -->
    <script type="application/ld+json">
    [
        {json_ld_combined}
    ]
    </script>
</head>
<body>
    <div class="container mt-4">
        <header class="text-center mb-5">
            <h1 class="text-primary old-london">Auscheckt is</h1>
            <p class="text-primary"><strong>Wo auscheckt is, wo ausg'steckt is.</strong></p>
            <nav>
                <a href="/" class="btn btn-outline-primary">← Zurück zur Übersicht</a>
            </nav>
        </header>
        
        <main>
            <h2 class="mb-4">Heurigen am {date_german}</h2>
            
            {f'<div id="map" class="mb-4" style="height: 400px;"></div>' if map_markers else ''}
            
            <div class="events-list">
                {events_html}
            </div>
        </main>
        
        <footer class="text-center mt-5 py-4 border-top" style="background-color: #f1f1f1;">
            <p><small>Open-Source-Projekt für Heurigenliebhaber:innen und Aficionados.</small></p>
            <p><small><a href="https://github.com/sektionschef/auschecktis">GitHub Repo</a></small></p>
        </footer>
    </div>
    
    <!-- JavaScript -->
    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
    <script>
        {map_js}
    </script>
</body>
</html>'''
        
        return html_template
    
    def generate_map_js(self, markers: List[Dict[str, Any]]) -> str:
        """Generate JavaScript for Leaflet map"""
        if not markers:
            return ''
        
        markers_js = []
        for marker in markers:
            popup_html = f"""<strong>{marker['title']}</strong><br>
            <a href="{marker['url']}" target="_blank" style="color:#457c43;text-decoration:underline;">Website</a>"""
            if marker.get('mapLink'):
                popup_html += f""" &middot; 
                <a href="{marker['mapLink']}" target="_blank" style="color:#457c43;text-decoration:underline;">Google Maps</a>"""
            
            markers_js.append(f"""
            L.marker([{marker['lat']}, {marker['lng']}], {{icon: greenIcon}})
                .bindPopup(`{popup_html}`)
                .addTo(map);""")
        
        bounds = [[m['lat'], m['lng']] for m in markers]
        
        return f'''
        // Initialize map
        const map = L.map('map').setView([48.3006, 16.3906], 13);
        
        L.tileLayer('https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png', {{
            attribution: '&copy; OpenStreetMap contributors'
        }}).addTo(map);
        
        // Custom green icon
        const greenIcon = L.icon({{
            iconUrl: 'data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" width="32" height="48" viewBox="0 0 32 48"><path fill="%23457c43" stroke="white" stroke-width="2" d="M16 2C8.268 2 2 8.268 2 16c0 10.493 12.03 28.01 12.53 28.74a2 2 0 0 0 3.94 0C17.97 44.01 30 26.493 30 16c0-7.732-6.268-14-14-14zm0 20a6 6 0 1 1 0-12 6 6 0 0 1 0 12z"/></svg>',
            iconSize: [32, 48],
            iconAnchor: [16, 47],
            popupAnchor: [0, -40]
        }});
        
        // Add markers
        {''.join(markers_js)}
        
        // Fit bounds if multiple markers
        {f"map.fitBounds({bounds}, {{padding: [20, 20]}});" if len(markers) > 1 else ""}
        '''
    
    def generate_index_page(self, events: List[Dict[str, Any]]) -> str:
        """Generate main index page with interactive map and date navigation"""
        today = datetime.now().date()
        
        # Generate all events data as JSON for JavaScript
        events_json = json.dumps(events, ensure_ascii=False, indent=2)
        
        return f'''<!DOCTYPE html>
<html lang="de">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Heurigenkalender Stammersdorf mit Ausg'steckt Zeiten</title>
    <meta name="description" content="Welcher Heurige hat ausg'steckt? Der aktuelle Heurigenkalender für Stammersdorf mit allen Öffnungszeiten, Standorte und Termine.">
    
    <!-- Favicons -->
    <link rel="icon" type="image/png" href="/favicon-96x96.png" sizes="96x96" />
    <link rel="icon" type="image/svg+xml" href="/favicon.svg" />
    <link rel="shortcut icon" href="/favicon.ico" />
    <link rel="apple-touch-icon" sizes="180x180" href="/apple-touch-icon.png" />
    <link rel="manifest" href="/site.webmanifest" />
    
    <!-- CSS -->
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
    <link rel="stylesheet" href="/custom.css">
</head>
<body>
    <div id="main">
        <div class="mb-5 container text-center">
            <h1 class="text-primary old-london">Auscheckt is</h1>
            <p class="text-primary"><strong>Wo auscheckt is, wo ausg'steckt is.</strong></p>
        </div>
        <div class="container text-center mb-4">
            <p>Der Heurigenkalender zeigt die <strong>Öffnungszeiten und Standorte</strong> der schönsten Heurigen in <strong>Stammersdorf</strong>. Die Öffnungszeiten werden regelmäßig automatisch von den Webseiten der Heurigen und dem <a href="http://weinort-stammersdorf.at/weinbau/wp-content/uploads/2021/03/Heurigenkalender-2025_v3-druck.pdf" target="_blank">offiziellen Kalender</a> aktualisiert.</p>
        </div>
        <div id="open-today" class="container text-center mb-4">
            <div class="mb-4">
                <button id="prev-day" class="btn btn-primary btn-lg rounded-circle me-2 d-inline-flex align-items-center justify-content-center" style="width:2.5em; height:2.5em;" disabled title="Vortag">
                    <span class="visually-hidden">Vortag</span>
                    <svg xmlns="http://www.w3.org/2000/svg" width="1.5em" height="1.5em" fill="currentColor" viewBox="0 0 16 16">
                        <path fill-rule="evenodd" d="M11.354 1.646a.5.5 0 0 1 0 .708L5.707 8l5.647 5.646a.5.5 0 0 1-.708.708l-6-6a.5.5 0 0 1 0-.708l6-6a.5.5 0 0 1 .708 0z"/>
                    </svg>
                </button>
                <button id="next-day" class="btn btn-primary btn-lg rounded-circle d-inline-flex align-items-center justify-content-center" style="width:2.5em; height:2.5em;" title="Nächster Tag">
                    <span class="visually-hidden">Nächster Tag</span>
                    <svg xmlns="http://www.w3.org/2000/svg" width="1.5em" height="1.5em" fill="currentColor" viewBox="0 0 16 16">
                        <path fill-rule="evenodd" d="M4.646 14.354a.5.5 0 0 1 0-.708L10.293 8 4.646 2.354a.5.5 0 1 1 .708-.708l6 6a.5.5 0 0 1 0 .708l-6 6a.5.5 0 0 1-.708 0z"/>
                    </svg>
                </button>
            </div>
            <h2 class="mb-4 text-primary"><span id="current-date"></span></h2>
            <div id="map" class="mb-4" style="height: 320px; width: 100%; margin-bottom: 1em;"></div>
            <ul id="open-today-list" class="list-unstyled text-start mx-auto" style="max-width: 300px;"></ul>
        </div>
    </div>
    <footer class="text-center mt-5 py-4 border-top" style="background-color: #f1f1f1;">
        <p>
            <small>Open-Source-Projekt für Heurigenliebhaber:innen und Aficionados.</small>
        </p>
        <p>
            <small><img src="assets/github-mark.svg" alt="GitHub" style="height: 1em; vertical-align: middle; margin-right: 0.3em;"> <a href="https://github.com/sektionschef/auschecktis">GitHub Repo</a></small>
        </p>
    </footer>
    
    <!-- JavaScript -->
    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
    <script>
        // All events data
        const allEvents = {events_json};
        
        // Wait for DOM to be ready
        document.addEventListener('DOMContentLoaded', function() {{
            const today = new Date();
            const maxDate = new Date(today);
            maxDate.setDate(today.getDate() + 7);
            
            let currentDate = new Date(today);
            
            const ul = document.getElementById('open-today-list');
            const currentDateSpan = document.getElementById('current-date');
            const prevBtn = document.getElementById('prev-day');
            const nextBtn = document.getElementById('next-day');
            
            function formatDate(date) {{
                return date.toLocaleDateString('de-AT', {{ weekday: 'long', year: 'numeric', month: '2-digit', day: '2-digit' }});
            }}
            
            function getISO(date) {{
                return date.toISOString().slice(0, 10);
            }}
            
            // Initialize map
            let map = L.map('map').setView([48.3006, 16.3906], 13); // Center on Stammersdorf
            
            L.tileLayer('https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png', {{
                attribution: '&copy; OpenStreetMap contributors'
            }}).addTo(map);
            
            let markerGroup = L.layerGroup().addTo(map);
            
            function clearMarkers() {{
                markerGroup.clearLayers();
            }}
            
            function addMarker(lat, lng, popupHtml) {{
                L.marker([lat, lng], {{ icon: greenIcon }}).bindPopup(popupHtml).addTo(markerGroup);
            }}
            
            // Custom green icon
            const greenIcon = L.icon({{
                iconUrl: 'data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" width="32" height="48" viewBox="0 0 32 48"><path fill="%23457c43" stroke="white" stroke-width="2" d="M16 2C8.268 2 2 8.268 2 16c0 10.493 12.03 28.01 12.53 28.74a2 2 0 0 0 3.94 0C17.97 44.01 30 26.493 30 16c0-7.732-6.268-14-14-14zm0 20a6 6 0 1 1 0-12 6 6 0 0 1 0 12z"/></svg>',
                iconSize:     [32, 48],
                iconAnchor:   [16, 47],
                popupAnchor:  [0, -40]
            }});
            
            function renderList() {{
                const currentISO = getISO(currentDate);
                const todayISO = getISO(today);
                const tomorrow = new Date(today);
                tomorrow.setDate(today.getDate() + 1);
                const tomorrowISO = getISO(tomorrow);
            
                // Set heading text
                if (currentISO === todayISO) {{
                    currentDateSpan.textContent = "Heute geöffnet";
                }} else if (currentISO === tomorrowISO) {{
                    currentDateSpan.textContent = "Morgen geöffnet";
                }} else {{
                    currentDateSpan.textContent = "Geöffnet am " + formatDate(currentDate);
                }}
            
                // Enable/disable prev/next buttons
                prevBtn.disabled = currentISO <= todayISO;
                nextBtn.disabled = currentISO >= getISO(maxDate);
            
                // Filter for current date
                const openToday = allEvents.filter(event => event.start.slice(0, 10) === currentISO);
            
                ul.innerHTML = '';
                clearMarkers();
            
                if (openToday.length === 0) {{
                    ul.innerHTML = '<li>Kein Heuriger geöffnet.</li>';
                }} else {{
                    let bounds = [];
                    openToday.forEach(event => {{
                        const li = document.createElement('li');
                        li.innerHTML = `<strong><a href="${{event.url}}" target="_blank">${{event.title}}</a></strong> 
            (ab ${{new Date(event.start).toLocaleTimeString('de-AT', {{hour: '2-digit', minute:'2-digit', hour12: false}})}} Uhr)`;
                        ul.appendChild(li);
            
                        // Add marker if possible
                        if (
                            event.extendedProps &&
                            typeof event.extendedProps.lat === "number" &&
                            typeof event.extendedProps.lng === "number"
                        ) {{
                            const latlng = [event.extendedProps.lat, event.extendedProps.lng];
                            addMarker(
                                latlng[0],
                                latlng[1],
                                `<strong>${{event.title}}</strong><br>
                                <a href="${{event.url}}" target="_blank" style="color:#457c43;text-decoration:underline;">Website</a> &middot; 
                                <a href="${{event.extendedProps.mapLink}}" target="_blank" style="color:#457c43;text-decoration:underline;">Google Maps</a>`
                            );
                            bounds.push(latlng);
                        }} else if (event.extendedProps && event.extendedProps.mapLink) {{
                            const latlng = extractLatLng(event.extendedProps.mapLink);
                            if (latlng) {{
                                addMarker(latlng[0], latlng[1], `<strong>${{event.title}}</strong><br><a href="${{event.url}}" target="_blank">Website</a>`);
                                bounds.push(latlng);
                            }}
                        }}
                    }});
                    // Zoom to bounds if markers exist
                    if (bounds.length > 0) {{
                        map.fitBounds(bounds, {{padding: [30, 30]}});
                    }} else {{
                        map.setView([48.3006, 16.3906], 13);
                    }}
                }}
            }}
            
            // Helper to extract lat/lng from Google Maps short links
            function extractLatLng(mapLink) {{
                try {{
                    if (mapLink.includes('@')) {{
                        const match = mapLink.match(/@([0-9\\.\\-]+),([0-9\\.\\-]+)/);
                        if (match) return [parseFloat(match[1]), parseFloat(match[2])];
                    }}
                }} catch (e) {{}}
                return null;
            }}
            
            // Initialize and render
            renderList();
            
            prevBtn.addEventListener('click', () => {{
                if (getISO(currentDate) > getISO(today)) {{
                    currentDate.setDate(currentDate.getDate() - 1);
                    renderList();
                }}
            }});
            
            nextBtn.addEventListener('click', () => {{
                if (getISO(currentDate) < getISO(maxDate)) {{
                    currentDate.setDate(currentDate.getDate() + 1);
                    renderList();
                }}
            }});
        }});
    </script>
    <!-- GoatCounter -->
    <script data-goatcounter="https://auschecktis.goatcounter.com/count"
       async
       src="//gc.zgo.at/count.js"></script>
</body>
</html>'''
    
    def copy_static_assets(self):
        """Copy static assets to output directory"""
        import shutil
        
        # List of static files to copy from assets directory
        static_files = [
            # CSS files
            ('input/assets/custom.css', 'custom.css'),
            # Icon files  
            ('input/assets/favicon.ico', 'favicon.ico'),
            ('input/assets/favicon.svg', 'favicon.svg'),
            ('input/assets/favicon-96x96.png', 'favicon-96x96.png'),
            ('input/assets/apple-touch-icon.png', 'apple-touch-icon.png'),
            ('input/assets/web-app-manifest-192x192.png', 'web-app-manifest-192x192.png'),
            ('input/assets/web-app-manifest-512x512.png', 'web-app-manifest-512x512.png'),
            ('input/assets/site.webmanifest', 'site.webmanifest'),
            # Other files
            ('input/assets/robots.txt', 'robots.txt'),
            ('input/assets/CNAME', 'CNAME'),
        ]
        
        # Copy individual files
        for src, dst in static_files:
            src_path = os.path.join(self.base_dir, src)
            dst_path = os.path.join(self.output_dir, dst)
            
            if os.path.exists(src_path):
                try:
                    shutil.copy2(src_path, dst_path)
                    print(f"📄 Copied {dst}")
                except Exception as e:
                    print(f"⚠️  Warning: Could not copy {src}: {e}")
        
        # Copy entire assets directory (for subdirectories like fonts)
        assets_src = os.path.join(self.base_dir, 'input', 'assets')
        assets_dst = os.path.join(self.output_dir, 'assets')
        if os.path.exists(assets_src):
            try:
                # Remove existing assets directory to avoid conflicts
                if os.path.exists(assets_dst):
                    shutil.rmtree(assets_dst)
                
                # Copy assets directory, excluding files already copied individually
                shutil.copytree(assets_src, assets_dst, dirs_exist_ok=True)
                print("📁 Copied assets directory")
                
                # Remove the duplicated files from assets (since they're copied to root)
                for _, dst in static_files:
                    duplicate_path = os.path.join(assets_dst, os.path.basename(dst))
                    if os.path.exists(duplicate_path):
                        os.remove(duplicate_path)
                        
            except Exception as e:
                print(f"⚠️  Warning: Could not copy assets: {e}")
    
    def build_site(self):
        """Build the complete static site"""
        print("🏗️  Building static site...")
        
        # Create output directory
        os.makedirs(self.output_dir, exist_ok=True)
        os.makedirs(os.path.join(self.output_dir, 'day'), exist_ok=True)
        
        # Load all events
        events = self.load_all_events()
        print(f"📅 Loaded {len(events)} events")
        
        # Generate index page
        index_html = self.generate_index_page(events)
        with open(os.path.join(self.output_dir, 'index.html'), 'w', encoding='utf-8') as f:
            f.write(index_html)
        print("📄 Generated index.html")
        
        # Generate daily pages for next 30 days
        today = datetime.now().date()
        for i in range(30):
            date = today + timedelta(days=i)
            daily_html = self.generate_daily_page(datetime.combine(date, datetime.min.time()), events)
            filename = f"{date.strftime('%Y-%m-%d')}.html"
            
            with open(os.path.join(self.output_dir, 'day', filename), 'w', encoding='utf-8') as f:
                f.write(daily_html)
        
        print("📅 Generated 30 daily pages")
        
        # Copy static assets
        self.copy_static_assets()
        
        print(f"✅ Site built in {self.output_dir}/")


if __name__ == "__main__":
    generator = HeurigenSiteGenerator()
    generator.build_site()