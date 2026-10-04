#!/usr/bin/env python3
"""
Static Site Generator for AusCheckt Is
Converts JSON event data to SEO-optimized static HTML with structured data
"""

import html
import json
import os
import subprocess
from urllib.parse import quote
from datetime import datetime, timedelta
from typing import Dict, List, Any
from zoneinfo import ZoneInfo


# Reports ("Heurigen melden") go to this address. It is only assembled by
# assets/app.js, so it never appears as plain text in the HTML.
CONTACT_EMAIL = "the.stevee@gmail.com"
GITHUB_REPO = "https://github.com/sektionschef/auschecktis"


def vienna_today():
    """Current date in Vienna (the CI runner uses UTC)"""
    return datetime.now(ZoneInfo("Europe/Vienna")).date()


class HeurigenSiteGenerator:
    def __init__(self, base_dir: str = "."):
        self.base_dir = base_dir
        self.data_dir = os.path.join(base_dir, "data")
        self.input_dir = os.path.join(base_dir, "input")
        self.output_dir = os.path.join(base_dir, "generated")

        # Load master heurigen data
        with open(
            os.path.join(self.input_dir, "heurigen_list.json"), "r", encoding="utf-8"
        ) as f:
            self.heurigen_master = json.load(f)

    def load_all_events(self) -> List[Dict[str, Any]]:
        """Load all events from data/*.json files"""
        all_events = []

        for filename in os.listdir(self.data_dir):
            if filename.endswith(".json") and filename != "archive":
                heurigen_key = filename.replace(".json", "")
                file_path = os.path.join(self.data_dir, filename)

                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        events = json.load(f)

                    # Add heurigen metadata to each event
                    for event in events:
                        # Normalize legacy schema fields from extendedProps.
                        # Older event files may only store location data there.
                        extended = event.get("extendedProps", {})
                        if isinstance(extended, dict):
                            if "mapLink" not in event and "mapLink" in extended:
                                event["mapLink"] = extended["mapLink"]
                            if "lat" not in event and "lat" in extended:
                                event["lat"] = extended["lat"]
                            if "lng" not in event and "lng" in extended:
                                event["lng"] = extended["lng"]

                        event["heurigen_key"] = heurigen_key
                        if heurigen_key in self.heurigen_master:
                            heurigen_data = self.heurigen_master[heurigen_key]
                            event["heurigen_data"] = heurigen_data

                            # Keep marker placement consistent by taking coordinates
                            # from the master heurigen list when available.
                            if heurigen_data.get("lat") is not None:
                                event["lat"] = heurigen_data["lat"]
                            if heurigen_data.get("lng") is not None:
                                event["lng"] = heurigen_data["lng"]

                            if heurigen_data.get("location"):
                                event["mapLink"] = heurigen_data["location"]

                            # The master list is the source of truth for the website.
                            if heurigen_data.get("website"):
                                event["url"] = heurigen_data["website"]
                        all_events.append(event)

                except Exception as e:
                    print(f"Error loading {filename}: {e}")

        # Sort events by start date
        all_events.sort(key=lambda x: x["start"])
        return all_events

    def generate_json_ld(self, event: Dict[str, Any]) -> str:
        """Generate JSON-LD structured data for an event"""
        heurigen_data = event.get("heurigen_data", {})

        json_ld = {
            "@context": "https://schema.org",
            "@type": "Event",
            "name": f"{event['title']} - Ausg'steckt",
            "description": f"Der Heurige {event['title']} hat ausg'steckt in Stammersdorf, Wien",
            "startDate": event["start"],
            "endDate": event["end"],
            "eventStatus": "https://schema.org/EventScheduled",
            "eventAttendanceMode": "https://schema.org/OfflineEventAttendanceMode",
            "location": {
                "@type": "Place",
                "name": event["title"],
                "address": {
                    "@type": "PostalAddress",
                    "addressLocality": "Wien",
                    "addressRegion": "Wien",
                    "addressCountry": "AT",
                    "postalCode": "1210",
                },
            },
            "url": event.get("url", ""),
            "organizer": {
                "@type": "Organization",
                "name": event["title"],
                "url": event.get("url", ""),
            },
        }

        # Add coordinates if available
        if "lat" in event and "lng" in event:
            json_ld["location"]["geo"] = {
                "@type": "GeoCoordinates",
                "latitude": event["lat"],
                "longitude": event["lng"],
            }

        return json.dumps(json_ld, indent=2, ensure_ascii=False)

    WEEKDAYS = ["Montag", "Dienstag", "Mittwoch", "Donnerstag", "Freitag", "Samstag", "Sonntag"]
    MONTHS = [
        "Jänner", "Februar", "März", "April", "Mai", "Juni",
        "Juli", "August", "September", "Oktober", "November", "Dezember",
    ]

    def format_date_german(self, date_str: str) -> str:
        """Format ISO date to German format, e.g. "Samstag, 10. Oktober 2026" """
        dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        return f"{self.WEEKDAYS[dt.weekday()]}, {dt.day}. {self.MONTHS[dt.month - 1]} {dt.year}"

    def format_time_german(self, date_str: str) -> str:
        """Format ISO time to German format"""
        dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        return dt.strftime("%H:%M")

    def format_opening_hours(self, event: Dict[str, Any]) -> str:
        """Opening hours label, e.g. "14:00–22:00 Uhr" or "ab 14:00 Uhr" without a fixed end"""
        start_time = self.format_time_german(event["start"])
        end_time = self.format_time_german(event["end"])
        if end_time == "23:59":
            return f"ab {start_time} Uhr"
        return f"{start_time}–{end_time} Uhr"

    def data_last_checked(self) -> str:
        """Date of the last commit touching the opening-hours data, e.g. "4. Oktober 2026" """
        try:
            out = subprocess.run(
                ["git", "log", "-1", "--format=%cs", "--", "data", "input/heurigen_list.json"],
                cwd=self.base_dir, capture_output=True, text=True, check=True,
            ).stdout.strip()
            dt = datetime.strptime(out, "%Y-%m-%d")
            return f"{dt.day}. {self.MONTHS[dt.month - 1]} {dt.year}"
        except Exception:
            return ""

    def public_event(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """Only the fields the browser needs"""
        fields = ["title", "start", "end", "url", "mapLink", "lat", "lng"]
        return {f: event[f] for f in fields if f in event}

    def json_for_script(self, data: Any) -> str:
        """JSON that is safe to embed in a <script> tag"""
        return json.dumps(data, ensure_ascii=False).replace("</", "<\\/")

    def sort_day_events(self, events: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        return sorted(events, key=lambda e: (e["start"], e["title"]))

    def generate_event_html(self, event: Dict[str, Any], index: int) -> str:
        """HTML card for a single opening with microdata (same markup as assets/app.js)"""
        title = html.escape(event["title"])
        url = html.escape(event.get("url", ""))
        map_link = html.escape(event.get("mapLink", ""))
        route = f'<a class="btn" href="{map_link}" target="_blank" rel="noopener">Route</a>' if map_link else ""
        website = f'<a class="btn btn-ghost" href="{url}" target="_blank" rel="noopener" itemprop="url">Website</a>' if url else ""
        return f"""
            <li class="card" data-i="{index}" itemscope itemtype="https://schema.org/Event">
                <span class="card-num" aria-hidden="true">{index + 1}</span>
                <div class="card-body">
                    <h3 class="card-title" itemprop="name">{title}</h3>
                    <p class="card-hours"><time itemprop="startDate" datetime="{event['start']}">{self.format_opening_hours(event)}</time></p>
                    <meta itemprop="endDate" content="{event['end']}">
                    <span hidden itemprop="location" itemscope itemtype="https://schema.org/Place">
                        <meta itemprop="name" content="{title}">
                        <meta itemprop="address" content="1210 Wien, Österreich">
                    </span>
                </div>
                <div class="card-actions">{route}{website}</div>
            </li>"""

    def generate_head(self, title: str, description: str, canonical: str, extra: str = "") -> str:
        """Shared <head> for all pages"""
        title = html.escape(title)
        description = html.escape(description)
        return f"""<!DOCTYPE html>
<html lang="de">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <script>
        // Apply the saved theme before the first paint
        try {{
            var t = localStorage.getItem('theme');
            if (t === 'dark' || t === 'light') document.documentElement.dataset.theme = t;
        }} catch (e) {{}}
    </script>
    <meta name="description" content="{description}">
    <link rel="canonical" href="{canonical}">
    <meta name="theme-color" content="#faf8f3" media="(prefers-color-scheme: light)">
    <meta name="theme-color" content="#141714" media="(prefers-color-scheme: dark)">

    <!-- Social sharing -->
    <meta property="og:type" content="website">
    <meta property="og:locale" content="de_AT">
    <meta property="og:title" content="{title}">
    <meta property="og:description" content="{description}">
    <meta property="og:url" content="{canonical}">
    <meta property="og:image" content="https://auschecktis.at/web-app-manifest-512x512.png">

    <!-- Favicons -->
    <link rel="icon" type="image/png" href="/favicon-96x96.png" sizes="96x96" />
    <link rel="icon" type="image/svg+xml" href="/favicon.svg" />
    <link rel="shortcut icon" href="/favicon.ico" />
    <link rel="apple-touch-icon" sizes="180x180" href="/apple-touch-icon.png" />
    <link rel="manifest" href="/site.webmanifest" />

    <!-- CSS -->
    <link rel="preload" href="/assets/font_old_london/OldLondon.ttf" as="font" type="font/ttf" crossorigin>
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
    <link rel="stylesheet" href="/custom.css">
{extra}</head>"""

    def generate_header(self) -> str:
        return """
    <header class="site-header">
        <button type="button" class="theme-toggle" id="theme-toggle" aria-label="Dunkles Design einschalten" hidden></button>
        <a href="/" class="logo old-london">AusCheckt is</a>
        <p class="tagline">Wo auscheckt is, wo ausg'steckt is.</p>
    </header>"""

    def mail_link(self, label: str, subject: str, body: str, issue_title: str, css: str = "btn") -> str:
        """Mail link, filled in by assets/app.js; without JS it opens a GitHub issue"""
        user, domain = CONTACT_EMAIL.split("@")
        fallback = f"{GITHUB_REPO}/issues/new?title={quote(issue_title)}&body={quote(body)}"
        return (
            f'<a class="{css} js-mail" href="{html.escape(fallback)}" data-u="{html.escape(user)}" '
            f'data-d="{html.escape(domain)}" data-subject="{html.escape(subject)}" '
            f'data-body="{html.escape(body)}">{label}</a>'
        )

    def generate_report_box(self) -> str:
        new_body = (
            "Hallo!\n\nIch möchte einen Heurigen in Stammersdorf melden:\n\n"
            "Name:\nAdresse:\nWebsite:\nÖffnungszeiten / Ausg'steckt-Termine:\n\nDanke!"
        )
        fix_body = "Hallo!\n\nAuf AusCheckt is stimmt etwas nicht:\n\nHeuriger:\nDatum:\nWas ist falsch:\n\nDanke!"
        new_btn = self.mail_link("Heurigen melden", "Neuer Heuriger für AusCheckt is", new_body, "Neuer Heuriger: ")
        fix_btn = self.mail_link("Fehler melden", "Fehler auf AusCheckt is", fix_body, "Fehler: ", "btn btn-ghost")
        return f"""
        <section class="section report">
            <div>
                <h2>Fehlt ein Heuriger?</h2>
                <p>Du kennst einen Heurigen oder eine Buschenschank in Stammersdorf, die hier fehlt – oder eine Öffnungszeit stimmt nicht? Schreib uns, wir nehmen es gerne auf.</p>
            </div>
            <div class="report-actions">
                {new_btn}
                {fix_btn}
                <a class="report-alt" href="{GITHUB_REPO}/issues/new" target="_blank" rel="noopener">oder als GitHub-Issue melden</a>
            </div>
        </section>"""

    def generate_footer(self, last_checked: str) -> str:
        checked = f"Öffnungszeiten zuletzt geprüft am {last_checked}. " if last_checked else ""
        return f"""
    <footer class="site-footer">
        <p>{checked}Angaben ohne Gewähr – bei Schlechtwetter sperren manche Buschenschanken spontan zu, im Zweifel kurz anrufen.</p>
        <p>Open-Source-Projekt für Heurigenliebhaber:innen und Aficionados ·
            <a href="{GITHUB_REPO}"><img src="/assets/github-mark.svg" alt="" class="gh-icon">GitHub</a> ·
            {self.mail_link("Heurigen melden", "Neuer Heuriger für AusCheckt is", "Hallo!\n\nIch möchte einen Heurigen in Stammersdorf melden:\n\nName:\nAdresse:\nWebsite:\n", "Neuer Heuriger: ", "")}</p>
    </footer>"""

    def generate_scripts(self, data: Dict[str, Any]) -> str:
        return f"""
    <script id="ac-data" type="application/json">{self.json_for_script(data)}</script>
    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
    <script src="/assets/app.js"></script>
    <!-- GoatCounter -->
    <script data-goatcounter="https://auschecktis.goatcounter.com/count" async src="//gc.zgo.at/count.js"></script>"""

    def generate_daily_page(self, date: datetime, events: List[Dict[str, Any]], last_checked: str = "") -> str:
        """Generate HTML page for a specific date"""
        date_str = date.strftime("%Y-%m-%d")
        date_german = self.format_date_german(date.isoformat())

        day_events = self.sort_day_events([e for e in events if e["start"].startswith(date_str)])
        json_ld_combined = ",\n".join(self.generate_json_ld(event) for event in day_events)

        count = len(day_events)
        if count == 0:
            headline = "Kein Heuriger hat ausg'steckt"
        elif count == 1:
            headline = "1 Heuriger hat ausg'steckt"
        else:
            headline = f"{count} Heurige haben ausg'steckt"

        cards = "\n".join(self.generate_event_html(e, i) for i, e in enumerate(day_events))
        content = f"""
            <div class="layout">
                <ol class="cards" id="list">{cards}
                </ol>
                <div class="map-wrap"><div id="map" role="region" aria-label="Karte"></div></div>
            </div>""" if day_events else """
            <p class="empty">An diesem Tag hat laut unseren Daten kein Heuriger in Stammersdorf ausg'steckt.</p>"""

        head = self.generate_head(
            f"Heurigen in Stammersdorf am {date_german} – AusCheckt is",
            f"Welche Heurigen in Stammersdorf haben am {date_german} ausg'steckt? Öffnungszeiten, Karte und Route zu allen offenen Heurigen und Buschenschanken.",
            f"https://auschecktis.at/day/{date_str}.html",
            f"""    <script type="application/ld+json">
    [
        {json_ld_combined}
    ]
    </script>
""",
        )
        data = {"mode": "day", "date": date_str, "events": [self.public_event(e) for e in day_events]}

        return f"""{head}
<body>
    {self.generate_header()}
    <main class="wrap">
        <section class="answer">
            <p class="eyebrow">{date_german}</p>
            <h1 class="answer-title">{headline}</h1>
            <p class="answer-sub"><a href="/#{date_str}">← Alle Tage im Heurigenkalender</a></p>
        </section>
        {content}
    </main>
    {self.generate_footer(last_checked)}
    {self.generate_scripts(data)}
</body>
</html>"""

    def generate_index_page(self, events: List[Dict[str, Any]], last_checked: str = "") -> str:
        """Generate main index page: today's answer, day strip, list + map, all Heurigen"""
        today = vienna_today().isoformat()
        upcoming = [self.public_event(e) for e in events if e["start"][:10] >= today]
        today_events = self.sort_day_events([e for e in upcoming if e["start"][:10] == today])

        heurigen = sorted(
            (
                {"title": h["label"], "url": h.get("website", ""), "mapLink": h.get("location", "")}
                for h in self.heurigen_master.values()
            ),
            key=lambda h: h["title"].lower(),
        )

        # Server-rendered answer for today (replaced by assets/app.js, kept for SEO and without JS)
        count = len(today_events)
        if count == 0:
            headline = "Heute hat kein Heuriger ausg'steckt"
        elif count == 1:
            headline = "1 Heuriger hat heute ausg'steckt"
        else:
            headline = f"{count} Heurige haben heute ausg'steckt"
        cards = "\n".join(self.generate_event_html(e, i) for i, e in enumerate(today_events))
        all_items = "\n".join(
            f'                <li><span class="all-name">{html.escape(h["title"])}</span></li>' for h in heurigen
        )

        head = self.generate_head(
            "AusCheckt is – Welche Heurigen in Stammersdorf haben heute ausg'steckt?",
            "Welche Heurigen in Stammersdorf haben heute ausg'steckt? Der Heurigenkalender zeigt Öffnungszeiten, Karte und Route aller Heurigen und Buschenschanken in Stammersdorf – Tag für Tag.",
            "https://auschecktis.at/",
        )
        data = {"mode": "index", "today": today, "events": upcoming, "heurigen": heurigen}

        return f"""{head}
<body>
    {self.generate_header()}
    <main class="wrap">
        <section class="answer" aria-live="polite">
            <p class="eyebrow" id="day-label">Heute · {self.format_date_german(today)}</p>
            <h1 class="answer-title" id="day-title">{headline}</h1>
            <p class="answer-sub" id="day-sub">Heurigenkalender für Stammersdorf</p>
        </section>

        <nav class="day-strip" id="day-strip" aria-label="Tag auswählen"></nav>

        <div class="layout">
            <ol class="cards" id="list">{cards}
            </ol>
            <div class="map-wrap"><div id="map" role="region" aria-label="Karte der geöffneten Heurigen"></div></div>
        </div>

        <section class="section" id="alle">
            <h2>Wann hat mein Heuriger wieder offen?</h2>
            <p class="section-lead">Alle {len(heurigen)} Heurigen und Buschenschanken in Stammersdorf mit ihrem nächsten Termin.</p>
            <ul class="all-list" id="all-list">
{all_items}
            </ul>
        </section>

        {self.generate_report_box()}

        <section class="section why">
            <h2>Warum AusCheckt is?</h2>
            <ul class="why-grid">
                <li><strong>Eine Seite statt {len(heurigen)} Websites</strong><span>Alle Öffnungszeiten aus Stammersdorf an einem Ort – regelmäßig geprüft.</span></li>
                <li><strong>Das Wochenende planen</strong><span>Tipp oben auf einen Tag und sieh sofort, wer am Samstag ausg'steckt hat.</span></li>
                <li><strong>Immer griffbereit</strong><span>Zum Startbildschirm hinzufügen – dann ist der Heurigenkalender nur einen Tipp entfernt.</span></li>
                <li><strong>Frei &amp; offen</strong><span>Ohne Werbung, ohne Anmeldung, Open Source.</span></li>
            </ul>
        </section>
    </main>
    {self.generate_footer(last_checked)}
    {self.generate_scripts(data)}
</body>
</html>"""

    def copy_static_assets(self):
        """Copy static assets to output directory"""
        import shutil

        # List of static files to copy from assets directory
        static_files = [
            # CSS files
            ("input/assets/custom.css", "custom.css"),
            # Icon files
            ("input/assets/favicon.ico", "favicon.ico"),
            ("input/assets/favicon.svg", "favicon.svg"),
            ("input/assets/favicon-96x96.png", "favicon-96x96.png"),
            ("input/assets/apple-touch-icon.png", "apple-touch-icon.png"),
            (
                "input/assets/web-app-manifest-192x192.png",
                "web-app-manifest-192x192.png",
            ),
            (
                "input/assets/web-app-manifest-512x512.png",
                "web-app-manifest-512x512.png",
            ),
            ("input/assets/site.webmanifest", "site.webmanifest"),
            # Other files
            ("input/assets/robots.txt", "robots.txt"),
            ("input/assets/CNAME", "CNAME"),
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
        assets_src = os.path.join(self.base_dir, "input", "assets")
        assets_dst = os.path.join(self.output_dir, "assets")
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

    def generate_sitemap(self, start_date, end_date):
        """Generate XML sitemap for SEO"""

        base_url = "https://auschecktis.at"
        now = vienna_today().isoformat()

        sitemap_urls = []

        # Add homepage
        sitemap_urls.append(
            {"loc": base_url, "lastmod": now, "changefreq": "daily", "priority": "1.0"}
        )

        # Add all daily pages
        current_date = start_date
        while current_date <= end_date:
            date_str = current_date.strftime("%Y-%m-%d")
            sitemap_urls.append(
                {
                    "loc": f"{base_url}/day/{date_str}.html",
                    "changefreq": "daily",
                    "priority": "0.8",
                }
            )
            current_date += timedelta(days=1)

        # Generate XML
        sitemap_xml = '<?xml version="1.0" encoding="UTF-8"?>\n'
        sitemap_xml += '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'

        for url in sitemap_urls:
            sitemap_xml += "  <url>\n"
            sitemap_xml += f'    <loc>{url["loc"]}</loc>\n'
            if "lastmod" in url:
                sitemap_xml += f'    <lastmod>{url["lastmod"]}</lastmod>\n'
            sitemap_xml += f'    <changefreq>{url["changefreq"]}</changefreq>\n'
            sitemap_xml += f'    <priority>{url["priority"]}</priority>\n'
            sitemap_xml += "  </url>\n"

        sitemap_xml += "</urlset>\n"

        # Write sitemap
        sitemap_path = os.path.join(self.output_dir, "sitemap.xml")
        with open(sitemap_path, "w", encoding="utf-8") as f:
            f.write(sitemap_xml)

        print(f"🗺️  Generated sitemap.xml with {len(sitemap_urls)} URLs")

    def build_site(self):
        """Build the complete static site"""
        print("🏗️  Building static site...")

        # Create output directory
        os.makedirs(self.output_dir, exist_ok=True)
        os.makedirs(os.path.join(self.output_dir, "day"), exist_ok=True)

        # Load all events
        events = self.load_all_events()
        print(f"📅 Loaded {len(events)} events")

        # Generate index page
        last_checked = self.data_last_checked()
        index_html = self.generate_index_page(events, last_checked)
        with open(
            os.path.join(self.output_dir, "index.html"), "w", encoding="utf-8"
        ) as f:
            f.write(index_html)
        print("📄 Generated index.html")

        # Generate daily pages
        today = vienna_today()

        # Generate pages up to the latest event date
        latest_date = today
        for event in events:
            event_date = datetime.fromisoformat(
                event["start"].replace("Z", "+00:00")
            ).date()
            if event_date > latest_date:
                latest_date = event_date

        # Delete old HTML files (before today)
        day_dir = os.path.join(self.output_dir, "day")
        if os.path.exists(day_dir):
            deleted_count = 0
            for filename in os.listdir(day_dir):
                if filename.endswith(".html"):
                    # Extract date from filename
                    try:
                        file_date_str = filename.replace(".html", "")
                        file_date = datetime.strptime(file_date_str, "%Y-%m-%d").date()
                        if file_date < today:
                            os.remove(os.path.join(day_dir, filename))
                            deleted_count += 1
                    except:
                        pass
            if deleted_count > 0:
                print(f"🗑️  Deleted {deleted_count} old HTML pages")

        # Generate pages from today until the latest date
        current_date = today
        page_count = 0
        while current_date <= latest_date:
            daily_html = self.generate_daily_page(
                datetime.combine(current_date, datetime.min.time()), events, last_checked
            )
            filename = f"{current_date.strftime('%Y-%m-%d')}.html"

            with open(
                os.path.join(self.output_dir, "day", filename), "w", encoding="utf-8"
            ) as f:
                f.write(daily_html)

            current_date += timedelta(days=1)
            page_count += 1

        print(f"📅 Generated {page_count} daily pages (until {latest_date})")

        # Generate sitemap
        self.generate_sitemap(today, latest_date)

        # Copy static assets
        self.copy_static_assets()

        print(f"✅ Site built in {self.output_dir}/")


if __name__ == "__main__":
    generator = HeurigenSiteGenerator()
    generator.build_site()
