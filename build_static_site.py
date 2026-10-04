#!/usr/bin/env python3
"""
Static Site Generator for AusCheckt Is
Converts JSON event data to SEO-optimized static HTML with structured data
"""

import html
import json
import os
import re
import shutil
import subprocess
from datetime import date, datetime, timedelta
from typing import Dict, List, Any, Optional
from urllib.parse import quote
from zoneinfo import ZoneInfo

BASE_URL = "https://auschecktis.at"

# Reports ("Heurigen melden") go to this address. It is only assembled by
# assets/app.js, so it never appears as plain text in the HTML.
CONTACT_EMAIL = "the.stevee@gmail.com"
GITHUB_REPO = "https://github.com/sektionschef/auschecktis"

WEEKDAYS = ["Montag", "Dienstag", "Mittwoch", "Donnerstag", "Freitag", "Samstag", "Sonntag"]
WD_SHORT = ["Mo", "Di", "Mi", "Do", "Fr", "Sa", "So"]
SCHEMA_DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
MONTHS = [
    "Jänner", "Februar", "März", "April", "Mai", "Juni",
    "Juli", "August", "September", "Oktober", "November", "Dezember",
]


def vienna_today() -> date:
    """Current date in Vienna (the CI runner uses UTC)"""
    return datetime.now(ZoneInfo("Europe/Vienna")).date()


def slugify(text: str) -> str:
    """URL slug, e.g. "Biohof N°5" -> "biohof-n5", "Zur Christl" -> "zur-christl" """
    text = text.lower()
    for a, b in [("ä", "ae"), ("ö", "oe"), ("ü", "ue"), ("ß", "ss"), ("°", "")]:
        text = text.replace(a, b)
    return re.sub(r"[^a-z0-9]+", "-", text).strip("-")


def long_date(d: date, year: bool = True) -> str:
    """e.g. "Samstag, 10. Oktober 2026" """
    return f"{WEEKDAYS[d.weekday()]}, {d.day}. {MONTHS[d.month - 1]}" + (f" {d.year}" if year else "")


def short_date(d: date) -> str:
    """e.g. "Sa, 10.10." """
    return f"{WD_SHORT[d.weekday()]}, {d.day}.{d.month}."


def hours_label(event: Dict[str, Any]) -> str:
    """Opening hours label, e.g. "14:00–22:00 Uhr" or "ab 14:00 Uhr" without a fixed end"""
    start, end = event["start"][11:16], event["end"][11:16]
    return f"ab {start} Uhr" if end == "23:59" else f"{start}–{end} Uhr"


def event_date(event: Dict[str, Any]) -> date:
    return date.fromisoformat(event["start"][:10])


def esc(text: Any) -> str:
    """HTML-escape (attributes always use double quotes, so ' can stay as is)"""
    return html.escape(str(text), quote=False).replace('"', "&quot;")


class HeurigenSiteGenerator:
    def __init__(self, base_dir: str = "."):
        self.base_dir = base_dir
        self.data_dir = os.path.join(base_dir, "data")
        self.input_dir = os.path.join(base_dir, "input")
        self.output_dir = os.path.join(base_dir, "generated")
        self.today = vienna_today()

        # Load master heurigen data and give every Heuriger a page URL
        with open(os.path.join(self.input_dir, "heurigen_list.json"), "r", encoding="utf-8") as f:
            self.heurigen_master = json.load(f)
        for key, h in self.heurigen_master.items():
            h["key"] = key
            h["slug"] = slugify(h["label"])
            h["page"] = f"/heuriger/{h['slug']}/"

        feste_path = os.path.join(self.input_dir, "feste.json")
        self.feste = []
        if os.path.exists(feste_path):
            with open(feste_path, "r", encoding="utf-8") as f:
                self.feste = json.load(f)

        self.last_checked = self.data_last_checked()

    # ------------------------------------------------------------------ data

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

                    for event in events:
                        event["heurigen_key"] = heurigen_key
                        heurigen_data = self.heurigen_master.get(heurigen_key)
                        if heurigen_data:
                            # The master list is the source of truth for everything but the times
                            event["title"] = heurigen_data["label"]
                            event["url"] = heurigen_data.get("website", "")
                            event["mapLink"] = heurigen_data.get("location", "")
                            event["lat"] = heurigen_data.get("lat")
                            event["lng"] = heurigen_data.get("lng")
                            event["page"] = heurigen_data["page"]
                        all_events.append(event)

                except Exception as e:
                    print(f"Error loading {filename}: {e}")

        all_events.sort(key=lambda x: (x["start"], x["title"]))
        return all_events

    def data_last_checked(self) -> str:
        """Date of the last commit touching the opening-hours data, e.g. "4. Oktober 2026" """
        try:
            out = subprocess.run(
                ["git", "log", "-1", "--format=%cs", "--", "data", "input/heurigen_list.json"],
                cwd=self.base_dir, capture_output=True, text=True, check=True,
            ).stdout.strip()
            d = date.fromisoformat(out)
            return f"{d.day}. {MONTHS[d.month - 1]} {d.year}"
        except Exception:
            return ""

    def public_event(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """Only the fields the browser needs"""
        fields = ["title", "start", "end", "url", "mapLink", "lat", "lng", "page"]
        return {f: event[f] for f in fields if f in event and event[f] is not None}

    def events_on(self, events: List[Dict[str, Any]], d: date) -> List[Dict[str, Any]]:
        iso = d.isoformat()
        return [e for e in events if e["start"][:10] == iso]

    def next_opening(self, events: List[Dict[str, Any]], key: str) -> Optional[Dict[str, Any]]:
        today = self.today.isoformat()
        return next((e for e in events if e["heurigen_key"] == key and e["start"][:10] >= today), None)

    def full_address(self, h: Dict[str, Any]) -> str:
        street = h.get("address", "")
        return f"{street}, 1210 Wien" if street else "1210 Wien"

    def fest_dates(self, fest: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Festival dates as dicts with parsed start/end dates, sorted"""
        out = []
        for d in fest.get("dates", []):
            out.append({**d, "start_date": date.fromisoformat(d["start"][:10]),
                        "end_date": date.fromisoformat(d["end"][:10])})
        return sorted(out, key=lambda d: d["start_date"])

    def fest_label(self, d: Dict[str, Any]) -> str:
        """e.g. "Sa, 3. – So, 4. Oktober 2026, 13–22 Uhr" """
        s, e = d["start_date"], d["end_date"]
        if s == e:
            label = f"{long_date(s)}"
        elif s.month == e.month:
            label = f"{WD_SHORT[s.weekday()]}, {s.day}. – {WD_SHORT[e.weekday()]}, {e.day}. {MONTHS[e.month - 1]} {e.year}"
        else:
            label = f"{WD_SHORT[s.weekday()]}, {s.day}. {MONTHS[s.month - 1]} – {WD_SHORT[e.weekday()]}, {e.day}. {MONTHS[e.month - 1]} {e.year}"
        if len(d["start"]) > 10:
            label += f", {int(d['start'][11:13])}–{int(d['end'][11:13])} Uhr"
        return label

    # ------------------------------------------------------- structured data

    def json_ld(self, data: Any) -> str:
        return (
            '    <script type="application/ld+json">\n'
            + json.dumps(data, indent=2, ensure_ascii=False).replace("</", "<\\/")
            + "\n    </script>\n"
        )

    def postal_address(self, street: str) -> Dict[str, Any]:
        address = {
            "@type": "PostalAddress",
            "postalCode": "1210",
            "addressLocality": "Wien",
            "addressRegion": "Wien",
            "addressCountry": "AT",
        }
        if street:
            address["streetAddress"] = street
        return address

    def business_ld(self, h: Dict[str, Any], events: List[Dict[str, Any]] = None) -> Dict[str, Any]:
        """A Heuriger as Schema.org Winery with its upcoming opening hours"""
        ld = {
            "@type": "Winery",
            "@id": f"{BASE_URL}{h['page']}#heuriger",
            "name": h["label"],
            "url": f"{BASE_URL}{h['page']}",
            "address": self.postal_address(h.get("address", "")),
            "geo": {"@type": "GeoCoordinates", "latitude": h["lat"], "longitude": h["lng"]},
        }
        if h.get("website"):
            ld["sameAs"] = [h["website"]]
        if h.get("location"):
            ld["hasMap"] = h["location"]
        if events:
            # Opening hours change from week to week, so every opening day is
            # one specification valid for exactly that date (next 8 weeks)
            limit = (self.today + timedelta(days=56)).isoformat()
            ld["openingHoursSpecification"] = [
                {
                    "@type": "OpeningHoursSpecification",
                    "dayOfWeek": f"https://schema.org/{SCHEMA_DAYS[event_date(e).weekday()]}",
                    "opens": e["start"][11:16],
                    "closes": e["end"][11:16],
                    "validFrom": e["start"][:10],
                    "validThrough": e["start"][:10],
                }
                for e in events if e["start"][:10] <= limit
            ]
        return ld

    def item_list_ld(self, name: str, keys: List[str]) -> Dict[str, Any]:
        return {
            "@context": "https://schema.org",
            "@type": "ItemList",
            "name": name,
            "itemListElement": [
                {
                    "@type": "ListItem",
                    "position": i + 1,
                    "url": f"{BASE_URL}{self.heurigen_master[k]['page']}",
                    "name": self.heurigen_master[k]["label"],
                }
                for i, k in enumerate(keys)
            ],
        }

    def breadcrumb_ld(self, items: List[tuple]) -> Dict[str, Any]:
        return {
            "@context": "https://schema.org",
            "@type": "BreadcrumbList",
            "itemListElement": [
                {"@type": "ListItem", "position": i + 1, "name": name, "item": f"{BASE_URL}{url}"}
                for i, (name, url) in enumerate(items)
            ],
        }

    # ------------------------------------------------------------- partials

    def json_for_script(self, data: Any) -> str:
        """JSON that is safe to embed in a <script> tag"""
        return json.dumps(data, ensure_ascii=False).replace("</", "<\\/")

    def generate_event_html(self, event: Dict[str, Any], index: int) -> str:
        """HTML card for a single opening (same markup as assets/app.js)"""
        title = esc(event["title"])
        url = esc(event.get("url", ""))
        map_link = esc(event.get("mapLink", ""))
        page = esc(event.get("page", ""))
        name = f'<a href="{page}">{title}</a>' if page else title
        route = f'<a class="btn" href="{map_link}" target="_blank" rel="noopener">Route</a>' if map_link else ""
        website = f'<a class="btn btn-ghost" href="{url}" target="_blank" rel="noopener">Website</a>' if url else ""
        return f"""
            <li class="card" data-i="{index}">
                <span class="card-num" aria-hidden="true">{index + 1}</span>
                <div class="card-body">
                    <h3 class="card-title">{name}</h3>
                    <p class="card-hours"><time datetime="{event['start']}">{hours_label(event)}</time></p>
                </div>
                <div class="card-actions">{route}{website}</div>
            </li>"""

    def generate_head(self, title: str, description: str, path: str, extra: str = "", index: bool = True) -> str:
        """Shared <head> for all pages"""
        title = esc(title)
        description = esc(description)
        canonical = f"{BASE_URL}{path}"
        robots = "" if index else '    <meta name="robots" content="noindex, follow">\n'
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
{robots}    <link rel="canonical" href="{canonical}">
    <meta name="theme-color" content="#faf8f3" media="(prefers-color-scheme: light)">
    <meta name="theme-color" content="#141714" media="(prefers-color-scheme: dark)">

    <!-- Social sharing -->
    <meta property="og:type" content="website">
    <meta property="og:locale" content="de_AT">
    <meta property="og:site_name" content="AusCheckt is">
    <meta property="og:title" content="{title}">
    <meta property="og:description" content="{description}">
    <meta property="og:url" content="{canonical}">
    <meta property="og:image" content="{BASE_URL}/web-app-manifest-512x512.png">

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

    def generate_header(self, current: str = "") -> str:
        links = [("/heute/", "Heute"), ("/morgen/", "Morgen"), ("/wochenende/", "Wochenende"),
                 ("/#alle", "Alle Heurigen"), ("/#feste", "Feste")]
        current_attr = ' aria-current="page"'
        nav = " ".join(
            f'<a href="{url}"{current_attr if url == current else ""}>{label}</a>'
            for url, label in links
        )
        return f"""
    <header class="site-header">
        <button type="button" class="theme-toggle" id="theme-toggle" aria-label="Dunkles Design einschalten" hidden></button>
        <a href="/" class="logo old-london">AusCheckt is</a>
        <p class="tagline">Wo auscheckt is, wo ausg'steckt is.</p>
        <nav class="site-nav" aria-label="Hauptnavigation">{nav}</nav>
    </header>"""

    def mail_link(self, label: str, subject: str, body: str, issue_title: str, css: str = "btn") -> str:
        """Mail link, filled in by assets/app.js; without JS it opens a GitHub issue"""
        user, domain = CONTACT_EMAIL.split("@")
        fallback = f"{GITHUB_REPO}/issues/new?title={quote(issue_title)}&body={quote(body)}"
        return (
            f'<a class="{css} js-mail" href="{esc(fallback)}" data-u="{esc(user)}" '
            f'data-d="{esc(domain)}" data-subject="{esc(subject)}" '
            f'data-body="{esc(body)}">{label}</a>'
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

    def generate_footer(self) -> str:
        checked = f"Öffnungszeiten zuletzt geprüft am {self.last_checked}. " if self.last_checked else ""
        heurigen = " · ".join(
            f'<a href="{h["page"]}">{esc(h["label"])}</a>'
            for h in sorted(self.heurigen_master.values(), key=lambda h: h["label"].lower())
        )
        feste = " · ".join(f'<a href="/feste/{f["slug"]}/">{esc(f["name"])}</a>' for f in self.feste)
        return f"""
    <footer class="site-footer">
        <p class="footer-links"><strong>Heurige in Stammersdorf:</strong> {heurigen}</p>
        <p class="footer-links"><strong>Feste:</strong> {feste}</p>
        <p>{checked}Angaben ohne Gewähr – bei Schlechtwetter sperren manche Buschenschanken spontan zu, im Zweifel kurz anrufen.</p>
        <p>Open-Source-Projekt für Heurigenliebhaber:innen und Aficionados ·
            <a href="{GITHUB_REPO}"><img src="/assets/github-mark.svg" alt="" class="gh-icon">GitHub</a> ·
            {self.mail_link("Heurigen melden", "Neuer Heuriger für AusCheckt is", "Hallo!\n\nIch möchte einen Heurigen in Stammersdorf melden:\n\nName:\nAdresse:\nWebsite:\n", "Neuer Heuriger: ", "")}</p>
    </footer>"""

    def generate_scripts(self, data: Optional[Dict[str, Any]], leaflet: bool = True) -> str:
        data_tag = f'\n    <script id="ac-data" type="application/json">{self.json_for_script(data)}</script>' if data else ""
        leaflet_tag = '\n    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>' if leaflet else ""
        return f"""{data_tag}{leaflet_tag}
    <script src="/assets/app.js"></script>
    <!-- GoatCounter -->
    <script data-goatcounter="https://auschecktis.goatcounter.com/count" async src="//gc.zgo.at/count.js"></script>"""

    def page(self, head: str, body: str, data: Optional[Dict[str, Any]] = None, current: str = "",
             leaflet: bool = True) -> str:
        return f"""{head}
<body>
    {self.generate_header(current)}
    <main class="wrap">
{body}
    </main>
    {self.generate_footer()}
    {self.generate_scripts(data, leaflet)}
</body>
</html>"""

    def list_and_map(self, day_events: List[Dict[str, Any]], empty_text: str) -> str:
        if not day_events:
            return f'\n        <p class="empty">{empty_text}</p>'
        cards = "\n".join(self.generate_event_html(e, i) for i, e in enumerate(day_events))
        return f"""
        <div class="layout">
            <ol class="cards" id="list">{cards}
            </ol>
            <div class="map-wrap"><div id="map" role="region" aria-label="Karte"></div></div>
        </div>"""

    def count_headline(self, n: int, when: str = "") -> str:
        when = f"{when} " if when else ""
        if n == 0:
            return f"Kein Heuriger hat {when}ausg'steckt"
        if n == 1:
            return f"1 Heuriger hat {when}ausg'steckt"
        return f"{n} Heurige haben {when}ausg'steckt"

    # ---------------------------------------------------------------- pages

    def generate_index_page(self, events: List[Dict[str, Any]]) -> str:
        """Main page: today's answer, day strip, list + map, all Heurigen, festivals, FAQ"""
        today = self.today.isoformat()
        upcoming = [self.public_event(e) for e in events if e["start"][:10] >= today]
        today_events = self.events_on(events, self.today)

        heurigen = sorted(self.heurigen_master.values(), key=lambda h: h["label"].lower())
        heurigen_data = [
            {"title": h["label"], "url": h.get("website", ""), "mapLink": h.get("location", ""), "page": h["page"]}
            for h in heurigen
        ]

        # "Next opening" list, rendered at build time (assets/app.js adds the live status)
        all_items = []
        for h in heurigen:
            nxt = self.next_opening(events, h["key"])
            if nxt:
                d = event_date(nxt)
                when = "heute" if d == self.today else "morgen" if d == self.today + timedelta(days=1) else short_date(d)
                info = f'<span class="all-next">{when} ab {nxt["start"][11:16]}</span>'
            else:
                info = '<span class="all-none">derzeit keine Termine bekannt</span>'
            all_items.append(f'                <li><span class="all-name"><a href="{h["page"]}">{esc(h["label"])}</a></span>{info}</li>')

        feste_items = []
        for f in self.feste:
            dates = self.fest_dates(f)
            nxt = next((d for d in dates if d["end_date"] >= self.today), None)
            when = self.fest_label(nxt) if nxt else f"Termin {dates[-1]['start_date'].year + 1} folgt" if dates else ""
            feste_items.append(
                f'                <li><a href="/feste/{f["slug"]}/"><strong>{esc(f["name"])}</strong><span>{esc(when)}</span></a></li>'
            )

        ld = [
            {
                "@context": "https://schema.org",
                "@type": "WebSite",
                "name": "AusCheckt is",
                "alternateName": "Heurigenkalender Stammersdorf",
                "url": f"{BASE_URL}/",
                "inLanguage": "de-AT",
            },
            self.item_list_ld("Heurige und Buschenschanken in Stammersdorf", [h["key"] for h in heurigen]),
        ]
        head = self.generate_head(
            "AusCheckt is – Welche Heurigen in Stammersdorf haben heute ausg'steckt?",
            "Welche Heurigen in Stammersdorf haben heute ausg'steckt? Der Heurigenkalender zeigt Öffnungszeiten, Karte und Route aller Heurigen und Buschenschanken in Stammersdorf – Tag für Tag.",
            "/",
            self.json_ld(ld),
        )
        data = {"mode": "index", "today": today, "events": upcoming, "heurigen": heurigen_data}

        body = f"""
        <section class="answer" aria-live="polite">
            <p class="eyebrow" id="day-label">Heute · {long_date(self.today, year=False)}</p>
            <h1 class="answer-title" id="day-title">{self.count_headline(len(today_events), "heute")}</h1>
            <p class="answer-sub" id="day-sub">Heurigenkalender für Stammersdorf</p>
        </section>

        <nav class="day-strip" id="day-strip" aria-label="Tag auswählen"></nav>
{self.list_and_map(today_events, "Heute hat laut unseren Daten kein Heuriger in Stammersdorf ausg'steckt.")}

        <section class="section" id="alle">
            <h2>Wann hat mein Heuriger wieder offen?</h2>
            <p class="section-lead">Alle {len(heurigen)} Heurigen und Buschenschanken in Stammersdorf mit ihrem nächsten Termin.</p>
            <ul class="all-list" id="all-list">
{chr(10).join(all_items)}
            </ul>
        </section>

        <section class="section" id="feste">
            <h2>Feste in der Kellergasse</h2>
            <p class="section-lead">Mehrmals im Jahr feiert Stammersdorf – dann haben besonders viele Heurige und Weinkeller offen.</p>
            <ul class="fest-list">
{chr(10).join(feste_items)}
            </ul>
        </section>

        {self.generate_report_box()}

        {self.generate_faq()}

        <section class="section why">
            <h2>Warum AusCheckt is?</h2>
            <ul class="why-grid">
                <li><strong>Eine Seite statt {len(heurigen)} Websites</strong><span>Alle Öffnungszeiten aus Stammersdorf an einem Ort – regelmäßig geprüft.</span></li>
                <li><strong>Das Wochenende planen</strong><span>Tipp oben auf einen Tag und sieh sofort, wer am Samstag ausg'steckt hat.</span></li>
                <li><strong>Immer griffbereit</strong><span>Zum Startbildschirm hinzufügen – dann ist der Heurigenkalender nur einen Tipp entfernt.</span></li>
                <li><strong>Frei &amp; offen</strong><span>Ohne Werbung, ohne Anmeldung, Open Source.</span></li>
            </ul>
        </section>"""
        return self.page(head, body, data, current="/")

    def generate_faq(self) -> str:
        checked = f" Zuletzt geprüft am {self.last_checked}." if self.last_checked else ""
        faq = [
            ("Was bedeutet „ausg'steckt“?",
             "Hat ein Heuriger geöffnet, hängt er einen Buschen aus Föhrenzweigen über den Eingang – er hat „ausg'steckt“. "
             "Viele Heurige und Buschenschanken haben nur zu bestimmten Zeiten im Jahr offen, deshalb wechseln die Öffnungszeiten oft von Woche zu Woche."),
            ("Was ist der Unterschied zwischen Heurigem und Buschenschank?",
             "In einer Buschenschank schenkt die Winzerfamilie ihren eigenen Wein aus, dazu gibt es vor allem kalte Speisen vom Buffet. "
             "„Heuriger“ wird im Alltag für beides verwendet; viele Heurige haben zusätzlich eine warme Küche."),
            ("Wie komme ich zu den Heurigen in Stammersdorf?",
             "Am einfachsten mit den Straßenbahnlinien 30 und 31 bis zur Endstation Stammersdorf. Von dort sind die Stammersdorfer Kellergasse "
             "und die meisten Heurigen zu Fuß erreichbar. Bei jedem Heurigen findest du hier einen Link zur Route."),
            ("Haben die Heurigen in Stammersdorf auch im Winter offen?",
             "Einige ja – im Advent haben mehrere Heurige bis kurz vor Weihnachten ausg'steckt, viele machen im Jänner und Februar Pause. "
             "Im Kalender oben siehst du für jeden Tag, wer offen hat."),
            ("Wie aktuell sind die Öffnungszeiten?",
             "Die Termine stammen von den Websites der Heurigen und werden regelmäßig händisch geprüft." + checked +
             " Bei Schlechtwetter sperren manche Buschenschanken spontan zu – im Zweifel kurz anrufen."),
        ]
        items = "\n".join(
            f"""                <details>
                    <summary>{esc(q)}</summary>
                    <p>{esc(a)}</p>
                </details>"""
            for q, a in faq
        )
        return f"""<section class="section faq" id="faq">
            <h2>Häufige Fragen zum Heurigen in Stammersdorf</h2>
            <p class="section-lead">AusCheckt is ist der Heurigenkalender für Stammersdorf und die Stammersdorfer Kellergasse in Floridsdorf, dem 21. Bezirk von Wien.</p>
{items}
        </section>"""

    def generate_day_list_page(self, events: List[Dict[str, Any]], d: date, path: str, title: str,
                               question: str, when: str, current: str, index: bool = True) -> str:
        """List page for one day: /heute/, /morgen/ and the dated /day/ pages"""
        day_events = self.events_on(events, d)
        n = len(day_events)
        if n:
            sub = f"{n} {'Heuriger' if n == 1 else 'Heurige'} in Stammersdorf {'hat' if n == 1 else 'haben'} {when} ausg'steckt."
        else:
            sub = "Laut unseren Daten hat an diesem Tag kein Heuriger in Stammersdorf offen."
        empty = 'Schau im <a href="/">Kalender</a> nach, wann wieder Heurige offen haben.'
        head = self.generate_head(
            title,
            f"Welche Heurigen in Stammersdorf haben {when} ({long_date(d)}) ausg'steckt? Öffnungszeiten, Karte und Route zu allen offenen Heurigen und Buschenschanken.",
            path,
            self.json_ld(self.item_list_ld(f"Heurige in Stammersdorf am {long_date(d)}", [e["heurigen_key"] for e in day_events])) if n else "",
            index=index,
        )
        data = {"mode": "day", "date": d.isoformat(), "events": [self.public_event(e) for e in day_events]}
        body = f"""
        <section class="answer">
            <p class="eyebrow">{long_date(d)}</p>
            <h1 class="answer-title">{question}</h1>
            <p class="answer-sub">{sub}</p>
        </section>
{self.list_and_map(day_events, empty)}
        <p class="more-link"><a href="/#{d.isoformat()}">Alle Tage im Heurigenkalender →</a></p>"""
        return self.page(head, body, data, current=current)

    def weekend_dates(self) -> List[date]:
        """Friday to Sunday of the current weekend, or the next one (Mon–Thu)"""
        wd = self.today.weekday()
        start = self.today if wd >= 4 else self.today + timedelta(days=4 - wd)
        return [start + timedelta(days=i) for i in range(7 - start.weekday())]

    def generate_weekend_page(self, events: List[Dict[str, Any]]) -> str:
        days = self.weekend_dates()
        weekend_events = [e for d in days for e in self.events_on(events, d)]
        # Numbers in order of first appearance, so the first list reads 1, 2, 3 …
        keys = list(dict.fromkeys(e["heurigen_key"] for e in weekend_events))
        number = {k: i for i, k in enumerate(keys)}

        sections = []
        for d in days:
            day_events = self.events_on(events, d)
            if day_events:
                rows = "\n".join(
                    f"""                <li class="card card-compact" data-i="{number[e['heurigen_key']]}">
                    <span class="card-num" aria-hidden="true">{number[e['heurigen_key']] + 1}</span>
                    <div class="card-body">
                        <h3 class="card-title"><a href="{e['page']}">{esc(e['title'])}</a></h3>
                        <p class="card-hours">{hours_label(e)}</p>
                    </div>
                </li>"""
                    for e in day_events
                )
                content = f'<ol class="cards" id="list-{d.isoformat()}">\n{rows}\n            </ol>'
            else:
                content = '<p class="empty">Kein Heuriger hat ausg\'steckt.</p>'
            sections.append(f"""            <section class="weekend-day">
                <h2>{WEEKDAYS[d.weekday()]}, {d.day}. {MONTHS[d.month - 1]} <span class="weekend-count">{len(day_events)}</span></h2>
                {content}
            </section>""")

        span = f"{days[0].day}.{days[0].month}. – {days[-1].day}.{days[-1].month}.{days[-1].year}" if len(days) > 1 else long_date(days[0])
        n = len(keys)
        places = [
            {"title": self.heurigen_master[k]["label"], "lat": self.heurigen_master[k]["lat"],
             "lng": self.heurigen_master[k]["lng"], "url": self.heurigen_master[k].get("website", ""),
             "mapLink": self.heurigen_master[k].get("location", ""), "page": self.heurigen_master[k]["page"],
             "address": self.full_address(self.heurigen_master[k])}
            for k in keys
        ]
        head = self.generate_head(
            "Heurigen in Stammersdorf am Wochenende – AusCheckt is",
            f"Welche Heurigen in Stammersdorf haben am Wochenende ({span}) ausg'steckt? Alle offenen Heurigen und Buschenschanken für Freitag, Samstag und Sonntag mit Öffnungszeiten und Karte.",
            "/wochenende/",
            self.json_ld(self.item_list_ld(f"Heurige in Stammersdorf am Wochenende {span}", keys)) if keys else "",
        )
        body = f"""
        <section class="answer">
            <p class="eyebrow">Wochenende · {span}</p>
            <h1 class="answer-title">Welche Heurigen haben am Wochenende offen?</h1>
            <p class="answer-sub">{n} {'Heuriger' if n == 1 else 'Heurige'} in Stammersdorf {'hat' if n == 1 else 'haben'} an diesem Wochenende ausg'steckt.</p>
        </section>
        <div class="layout">
            <div class="weekend" id="list">
{chr(10).join(sections)}
            </div>
            <div class="map-wrap"><div id="map" role="region" aria-label="Karte"></div></div>
        </div>
        <p class="more-link"><a href="/">Zum Heurigenkalender →</a></p>"""
        return self.page(head, body, {"mode": "places", "events": places}, current="/wochenende/")

    def generate_heuriger_page(self, h: Dict[str, Any], events: List[Dict[str, Any]]) -> str:
        today = self.today.isoformat()
        upcoming = [e for e in events if e["heurigen_key"] == h["key"] and e["start"][:10] >= today]
        name = esc(h["label"])
        address = esc(self.full_address(h))

        if upcoming:
            nxt = upcoming[0]
            d = event_date(nxt)
            if d == self.today:
                status = f"Heute ausg'steckt: {hours_label(nxt)}"
            elif d == self.today + timedelta(days=1):
                status = f"Nächstes Mal ausg'steckt: morgen, {long_date(d, year=False)}, {hours_label(nxt)}"
            else:
                status = f"Nächstes Mal ausg'steckt: {long_date(d, year=False)}, {hours_label(nxt)}"

            # Upcoming dates grouped by month
            months = {}
            for e in upcoming:
                ed = event_date(e)
                months.setdefault((ed.year, ed.month), []).append(e)
            groups = []
            for (y, m), evs in months.items():
                today_attr = ' class="is-today"'
                rows = "\n".join(
                    f'                    <li{today_attr if e["start"][:10] == today else ""}>'
                    f'<span class="date-day">{short_date(event_date(e))}</span>'
                    f'<span class="date-hours">{hours_label(e)}</span></li>'
                    for e in evs
                )
                groups.append(f"""            <div class="month">
                <h3>{MONTHS[m - 1]} {y}</h3>
                <ul class="date-list">
{rows}
                </ul>
            </div>""")
            dates_html = "\n".join(groups)
            description = (f"{h['label']} in Stammersdorf ({self.full_address(h)}): {status}. "
                           f"Alle kommenden ausg'steckt-Termine, Öffnungszeiten, Karte und Route.")
        else:
            status = "Derzeit sind keine Termine bekannt."
            dates_html = '            <p class="empty">Derzeit sind keine kommenden Termine bekannt. Schau auf der Website des Heurigen nach oder melde uns neue Termine.</p>'
            description = (f"{h['label']} in Stammersdorf ({self.full_address(h)}): Öffnungszeiten, "
                           f"ausg'steckt-Termine, Karte und Route.")

        status_cls = " is-today" if upcoming and upcoming[0]["start"][:10] == today else ""
        website = f'<a class="btn btn-ghost" href="{esc(h["website"])}" target="_blank" rel="noopener">Website</a>' if h.get("website") else ""
        route = f'<a class="btn" href="{esc(h["location"])}" target="_blank" rel="noopener">Route</a>' if h.get("location") else ""
        others = " ".join(
            f'<a href="{o["page"]}">{esc(o["label"])}</a>'
            for o in sorted(self.heurigen_master.values(), key=lambda o: o["label"].lower()) if o["key"] != h["key"]
        )

        ld = [
            {"@context": "https://schema.org", **self.business_ld(h, upcoming)},
            self.breadcrumb_ld([("AusCheckt is", "/"), ("Heurige", "/#alle"), (h["label"], h["page"])]),
        ]
        head = self.generate_head(
            f"{h['label']} Stammersdorf – Öffnungszeiten & Termine | AusCheckt is",
            description,
            h["page"],
            self.json_ld(ld),
        )
        place = {"title": h["label"], "lat": h["lat"], "lng": h["lng"], "url": h.get("website", ""),
                 "mapLink": h.get("location", ""), "address": self.full_address(h)}
        body = f"""
        <nav class="breadcrumb" aria-label="Brotkrumen"><a href="/">Heurigenkalender</a> › <a href="/#alle">Heurige</a> › {name}</nav>
        <div class="layout layout-place">
            <section class="place">
                <p class="eyebrow">Heuriger in Stammersdorf</p>
                <h1 class="place-title">{name}</h1>
                <p class="place-address">{address}</p>
                <p class="place-status{status_cls}">{esc(status)}</p>
                <div class="card-actions">{route}{website}</div>
            </section>
            <div class="map-wrap"><div id="map" class="map-small" role="region" aria-label="Karte"></div></div>
        </div>

        <section class="section">
            <h2>Ausg'steckt-Termine</h2>
            <div class="months">
{dates_html}
            </div>
        </section>

        <section class="section">
            <h2>Weitere Heurige in Stammersdorf</h2>
            <p class="chip-links">{others}</p>
        </section>"""
        return self.page(head, body, {"mode": "places", "events": [place]})

    def generate_fest_page(self, fest: Dict[str, Any], events: List[Dict[str, Any]]) -> str:
        dates = self.fest_dates(fest)
        nxt = next((d for d in dates if d["end_date"] >= self.today), None)
        last = dates[-1] if dates else None
        name = esc(fest["name"])
        year = nxt["start_date"].year if nxt else (last["start_date"].year + 1 if last else self.today.year)

        ld = [self.breadcrumb_ld([("AusCheckt is", "/"), ("Feste", "/#feste"), (fest["name"], f"/feste/{fest['slug']}/")])]
        open_html = ""
        if nxt:
            when = self.fest_label(nxt)
            lead = f"Nächster Termin: <strong>{esc(when)}</strong>"
            # Real events, so Event markup is correct here
            ld.append({
                "@context": "https://schema.org",
                "@type": "Event",
                "name": f"{fest['name']} {nxt['start_date'].year}",
                "description": fest["description"],
                "startDate": nxt["start"],
                "endDate": nxt["end"],
                "eventStatus": "https://schema.org/EventScheduled",
                "eventAttendanceMode": "https://schema.org/OfflineEventAttendanceMode",
                "location": {
                    "@type": "Place",
                    "name": f"{fest['location']}, Stammersdorf",
                    "address": self.postal_address(fest["location"]),
                },
                "url": f"{BASE_URL}/feste/{fest['slug']}/",
            })
            # Which Heurigen have opened on the festival days (if we have data yet)
            blocks = []
            d = nxt["start_date"]
            while d <= nxt["end_date"]:
                day_events = self.events_on(events, d)
                if day_events:
                    rows = "\n".join(
                        f'                    <li><a href="{e["page"]}">{esc(e["title"])}</a> <span>{hours_label(e)}</span></li>'
                        for e in day_events
                    )
                    blocks.append(f"""            <div class="month">
                <h3>{long_date(d, year=False)}</h3>
                <ul class="fest-open">
{rows}
                </ul>
            </div>""")
                d += timedelta(days=1)
            if blocks:
                open_html = f"""
        <section class="section">
            <h2>Diese Heurigen haben offen</h2>
            <div class="months">
{chr(10).join(blocks)}
            </div>
        </section>"""
        else:
            lead = f"Der Termin für {year} steht noch nicht fest."
            if last:
                lead += f" Zuletzt: {esc(self.fest_label(last))}."

        head = self.generate_head(
            f"{fest['name']} {year} in Stammersdorf – Termin & offene Heurige | AusCheckt is",
            f"{fest['name']} {year} in Stammersdorf: Termin, Programm und welche Heurigen und Buschenschanken offen haben. {fest['description']}"[:300],
            f"/feste/{fest['slug']}/",
            self.json_ld(ld),
        )
        body = f"""
        <nav class="breadcrumb" aria-label="Brotkrumen"><a href="/">Heurigenkalender</a> › <a href="/#feste">Feste</a> › {name}</nav>
        <section class="answer answer-left">
            <p class="eyebrow">Fest in Stammersdorf · {esc(fest['location'])}</p>
            <h1 class="answer-title">{name} {year}</h1>
            <p class="answer-sub">{lead}</p>
        </section>
        <section class="section prose">
            <p>{esc(fest['description'])}</p>
            <p>Auch abseits der Feste haben in Stammersdorf viele Heurige offen – <a href="/heute/">wer heute ausg'steckt hat</a>, siehst du im Heurigenkalender.</p>
        </section>{open_html}"""
        return self.page(head, body, None, leaflet=False)

    def generate_404_page(self) -> str:
        head = self.generate_head("Seite nicht gefunden – AusCheckt is",
                                  "Diese Seite gibt es nicht (mehr).", "/404.html", index=False)
        body = """
        <section class="answer">
            <h1 class="answer-title">Hier hat niemand ausg'steckt.</h1>
            <p class="answer-sub">Diese Seite gibt es nicht (mehr) – vielleicht war es ein vergangener Tag.</p>
        </section>
        <p class="more-link"><a class="btn" href="/heute/">Wer hat heute offen?</a></p>"""
        return self.page(head, body, None, leaflet=False)

    # ---------------------------------------------------------------- build

    def write(self, rel_path: str, content: str):
        path = os.path.join(self.output_dir, rel_path)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)

    def copy_static_assets(self):
        """Copy static assets to output directory"""
        # Files that must live in the site root
        static_files = [
            "custom.css", "favicon.ico", "favicon.svg", "favicon-96x96.png", "apple-touch-icon.png",
            "web-app-manifest-192x192.png", "web-app-manifest-512x512.png", "site.webmanifest",
            "robots.txt", "CNAME",
        ]
        assets_src = os.path.join(self.input_dir, "assets")
        for name in static_files:
            src = os.path.join(assets_src, name)
            if os.path.exists(src):
                shutil.copy2(src, os.path.join(self.output_dir, name))

        # Everything else (fonts, app.js, icons) goes to /assets/
        assets_dst = os.path.join(self.output_dir, "assets")
        if os.path.exists(assets_dst):
            shutil.rmtree(assets_dst)
        shutil.copytree(assets_src, assets_dst, ignore=shutil.ignore_patterns(*static_files))
        print("📁 Copied static assets")

    def generate_sitemap(self, urls: List[tuple]):
        """XML sitemap: (path, changefreq, priority, has_lastmod)"""
        today = self.today.isoformat()
        lines = ['<?xml version="1.0" encoding="UTF-8"?>',
                 '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
        for path, changefreq, priority, lastmod in urls:
            lines.append("  <url>")
            lines.append(f"    <loc>{BASE_URL}{path}</loc>")
            if lastmod:
                lines.append(f"    <lastmod>{today}</lastmod>")
            lines.append(f"    <changefreq>{changefreq}</changefreq>")
            lines.append(f"    <priority>{priority}</priority>")
            lines.append("  </url>")
        lines.append("</urlset>")
        self.write("sitemap.xml", "\n".join(lines) + "\n")
        print(f"🗺️  Generated sitemap.xml with {len(urls)} URLs")

    def build_site(self):
        """Build the complete static site"""
        print("🏗️  Building static site...")
        os.makedirs(self.output_dir, exist_ok=True)

        events = self.load_all_events()
        print(f"📅 Loaded {len(events)} events")
        today = self.today
        tomorrow = today + timedelta(days=1)
        sitemap = [("/", "daily", "1.0", True)]

        self.write("index.html", self.generate_index_page(events))

        self.write("heute/index.html", self.generate_day_list_page(
            events, today, "/heute/", "Heurigen in Stammersdorf heute geöffnet – AusCheckt is",
            "Welche Heurigen haben heute ausg'steckt?", "heute", "/heute/"))
        self.write("morgen/index.html", self.generate_day_list_page(
            events, tomorrow, "/morgen/", "Heurigen in Stammersdorf morgen geöffnet – AusCheckt is",
            "Welche Heurigen haben morgen ausg'steckt?", "morgen", "/morgen/"))
        self.write("wochenende/index.html", self.generate_weekend_page(events))
        sitemap += [("/heute/", "daily", "0.9", True), ("/morgen/", "daily", "0.8", True),
                    ("/wochenende/", "daily", "0.9", True)]

        # One page per Heuriger (replaces pages of renamed/removed Heurigen)
        shutil.rmtree(os.path.join(self.output_dir, "heuriger"), ignore_errors=True)
        for h in sorted(self.heurigen_master.values(), key=lambda h: h["label"].lower()):
            self.write(f"heuriger/{h['slug']}/index.html", self.generate_heuriger_page(h, events))
            sitemap.append((h["page"], "daily", "0.8", True))
        print(f"🍷 Generated {len(self.heurigen_master)} Heurigen pages")

        shutil.rmtree(os.path.join(self.output_dir, "feste"), ignore_errors=True)
        for fest in self.feste:
            self.write(f"feste/{fest['slug']}/index.html", self.generate_fest_page(fest, events))
            sitemap.append((f"/feste/{fest['slug']}/", "weekly", "0.6", False))
        print(f"🎉 Generated {len(self.feste)} festival pages")

        # Dated day pages: kept for shared links, but not indexed (see /heute/, /morgen/)
        day_dir = os.path.join(self.output_dir, "day")
        shutil.rmtree(day_dir, ignore_errors=True)
        latest = max([event_date(e) for e in events] + [today])
        d = today
        count = 0
        while d <= latest:
            label = long_date(d)
            self.write(f"day/{d.isoformat()}.html", self.generate_day_list_page(
                events, d, f"/day/{d.isoformat()}.html", f"Heurigen in Stammersdorf am {label} – AusCheckt is",
                f"Welche Heurigen haben am {WEEKDAYS[d.weekday()]}, {d.day}. {MONTHS[d.month - 1]} ausg'steckt?",
                f"am {WEEKDAYS[d.weekday()]}", "", index=False))
            d += timedelta(days=1)
            count += 1
        print(f"📅 Generated {count} daily pages (until {latest})")

        self.write("404.html", self.generate_404_page())
        self.generate_sitemap(sitemap)
        self.copy_static_assets()
        print(f"✅ Site built in {self.output_dir}/")


if __name__ == "__main__":
    generator = HeurigenSiteGenerator()
    generator.build_site()
