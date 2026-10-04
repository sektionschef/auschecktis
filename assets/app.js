/*
 * AusCheckt is – client side of the Heurigenkalender.
 * Reads the embedded JSON (#ac-data) and renders the day strip, the list of
 * open Heurigen, the map and the "next opening" overview.
 * Index page: mode "index"; day pages: mode "day" (list is server-rendered);
 * Heuriger and weekend pages: mode "places" (map of places without times).
 */
(function () {
  'use strict';

  const dataEl = document.getElementById('ac-data');
  const DATA = dataEl ? JSON.parse(dataEl.textContent) : { mode: 'static', events: [] };
  const WEEKDAYS = ['Sonntag', 'Montag', 'Dienstag', 'Mittwoch', 'Donnerstag', 'Freitag', 'Samstag'];
  const WD_SHORT = ['So', 'Mo', 'Di', 'Mi', 'Do', 'Fr', 'Sa'];
  const MONTHS = ['Jänner', 'Februar', 'März', 'April', 'Mai', 'Juni', 'Juli', 'August',
    'September', 'Oktober', 'November', 'Dezember'];
  const CENTER = [48.3045, 16.405];

  // ---------- helpers ----------
  const pad = n => String(n).padStart(2, '0');
  // Local calendar date (not toISOString(), which is UTC)
  const isoDate = d => `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`;
  const parseDay = s => { const [y, m, d] = s.split('-').map(Number); return new Date(y, m - 1, d); };
  const addDays = (d, n) => { const x = new Date(d); x.setDate(x.getDate() + n); return x; };
  const time = s => s.slice(11, 16);
  const minutes = s => Number(s.slice(11, 13)) * 60 + Number(s.slice(14, 16));
  const hasEnd = e => time(e.end) !== '23:59';
  const esc = s => String(s).replace(/[&<>"']/g, c =>
    ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));

  const hoursLabel = e => hasEnd(e) ? `${time(e.start)}–${time(e.end)} Uhr` : `ab ${time(e.start)} Uhr`;
  const longDate = d => `${WEEKDAYS[d.getDay()]}, ${d.getDate()}. ${MONTHS[d.getMonth()]}`;
  const shortDate = d => `${d.getDate()}.${d.getMonth() + 1}.`;

  const now = new Date();
  const todayISO = isoDate(now);
  const tomorrowISO = isoDate(addDays(now, 1));
  const nowMin = now.getHours() * 60 + now.getMinutes();

  function relativeDay(iso) {
    if (iso === todayISO) return 'Heute';
    if (iso === tomorrowISO) return 'Morgen';
    return WEEKDAYS[parseDay(iso).getDay()];
  }

  // Live status – only meaningful for today
  function status(e, iso) {
    if (iso !== todayISO) return null;
    const start = minutes(e.start);
    const end = hasEnd(e) ? minutes(e.end) : 24 * 60;
    if (nowMin < start) return { cls: 'soon', text: `öffnet um ${time(e.start)}`, order: 1 };
    if (nowMin < end) return { cls: 'open', text: 'jetzt offen', order: 0 };
    return { cls: 'closed', text: 'heute schon zu', order: 2 };
  }

  function eventsOn(iso) {
    return DATA.events
      .filter(e => e.start.slice(0, 10) === iso)
      .sort((a, b) => a.start.localeCompare(b.start) || a.title.localeCompare(b.title));
  }

  function cardHTML(e, i, st) {
    const route = e.mapLink ? `<a class="btn" href="${esc(e.mapLink)}" target="_blank" rel="noopener">Route</a>` : '';
    const web = e.url ? `<a class="btn btn-ghost" href="${esc(e.url)}" target="_blank" rel="noopener">Website</a>` : '';
    const badge = st ? `<span class="badge badge-${st.cls}">${st.text}</span>` : '';
    return `<li class="card${st ? ' is-' + st.cls : ''}" data-i="${i}">
        <span class="card-num" aria-hidden="true">${i + 1}</span>
        <div class="card-body">
          <h3 class="card-title">${e.page ? `<a href="${esc(e.page)}">${esc(e.title)}</a>` : esc(e.title)}</h3>
          <p class="card-hours">${hoursLabel(e)}</p>
        </div>
        ${badge}
        <div class="card-actions">${route}${web}</div>
      </li>`;
  }

  // ---------- map ----------
  let map = null;
  let markers = [];

  function ensureMap() {
    const el = document.getElementById('map');
    if (!el || typeof L === 'undefined') return null;
    if (!map) {
      map = L.map(el, { scrollWheelZoom: false }).setView(CENTER, 14);
      L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '&copy; OpenStreetMap contributors',
        maxZoom: 19,
      }).addTo(map);
    }
    return map;
  }

  function renderMap(events, states) {
    const m = ensureMap();
    if (!m) return;
    markers.forEach(mk => mk.remove());
    markers = [];
    const bounds = [];
    events.forEach((e, i) => {
      if (typeof e.lat !== 'number' || typeof e.lng !== 'number') { markers.push(null); return; }
      const st = states[i];
      const icon = L.divIcon({
        className: 'pin-wrap',
        html: `<span class="pin${st ? ' pin-' + st.cls : ''}">${i + 1}</span>`,
        iconSize: [30, 30], iconAnchor: [15, 15], popupAnchor: [0, -16],
      });
      const links = [
        e.mapLink ? `<a href="${esc(e.mapLink)}" target="_blank" rel="noopener">Route</a>` : '',
        e.url ? `<a href="${esc(e.url)}" target="_blank" rel="noopener">Website</a>` : '',
      ].filter(Boolean).join(' · ');
      const mk = L.marker([e.lat, e.lng], { icon, title: e.title })
        .bindPopup(`<strong>${esc(e.title)}</strong><br>${e.start ? hoursLabel(e) : esc(e.address || '')}<br>${links}`)
        .addTo(m);
      mk.on('click', () => highlight(i, false));
      markers.push(mk);
      bounds.push([e.lat, e.lng]);
    });
    if (bounds.length > 1) m.fitBounds(bounds, { padding: [28, 28], maxZoom: 16 });
    else if (bounds.length === 1) m.setView(bounds[0], 16);
    else m.setView(CENTER, 14);
  }

  function highlight(i, fromList) {
    document.querySelectorAll('#list .card').forEach(c => c.classList.toggle('is-active', Number(c.dataset.i) === i));
    const mk = markers[i];
    if (fromList && mk && map) {
      map.panTo(mk.getLatLng());
      mk.openPopup();
    }
    if (!fromList) {
      const card = document.querySelector(`#list .card[data-i="${i}"]`);
      if (card) card.scrollIntoView({ block: 'nearest', behavior: 'smooth' });
    }
  }

  function bindList() {
    const list = document.getElementById('list');
    if (!list) return;
    list.addEventListener('click', ev => {
      if (ev.target.closest('a')) return;
      const card = ev.target.closest('.card');
      if (card) highlight(Number(card.dataset.i), true);
    });
  }

  // ---------- theme toggle ----------
  const SUN = '<svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" aria-hidden="true"><circle cx="12" cy="12" r="4.5"/><path d="M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4"/></svg>';
  const MOON = '<svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M20.5 14.5A8.5 8.5 0 0 1 9.5 3.5a8.5 8.5 0 1 0 11 11z"/></svg>';
  const toggle = document.getElementById('theme-toggle');
  const systemDark = window.matchMedia('(prefers-color-scheme: dark)');
  const isDark = () => (document.documentElement.dataset.theme || (systemDark.matches ? 'dark' : 'light')) === 'dark';

  function updateToggle() {
    const dark = isDark();
    toggle.innerHTML = dark ? SUN : MOON;
    toggle.setAttribute('aria-label', dark ? 'Helles Design einschalten' : 'Dunkles Design einschalten');
    toggle.title = toggle.getAttribute('aria-label');
  }

  if (toggle) {
    toggle.hidden = false;
    updateToggle();
    systemDark.addEventListener('change', updateToggle);
    toggle.addEventListener('click', () => {
      const next = isDark() ? 'light' : 'dark';
      document.documentElement.dataset.theme = next;
      try { localStorage.setItem('theme', next); } catch (e) { /* private mode */ }
      updateToggle();
    });
  }

  // ---------- report links (address assembled here to keep it out of the HTML) ----------
  document.querySelectorAll('.js-mail').forEach(a => {
    const to = `${a.dataset.u}@${a.dataset.d}`;
    a.href = `mailto:${to}?subject=${encodeURIComponent(a.dataset.subject)}&body=${encodeURIComponent(a.dataset.body)}`;
  });

  // ---------- pages without calendar data (festivals, 404) ----------
  if (DATA.mode === 'static') return;

  // ---------- day, Heuriger and weekend pages ----------
  if (DATA.mode === 'day' || DATA.mode === 'places') {
    const events = DATA.events;
    renderMap(events, events.map(() => null));
    bindList();
    return;
  }

  // ---------- index page ----------
  const days = [];
  const lastISO = DATA.events.reduce((max, e) => (e.start.slice(0, 10) > max ? e.start.slice(0, 10) : max), todayISO);
  for (let d = parseDay(todayISO); isoDate(d) <= lastISO; d = addDays(d, 1)) days.push(isoDate(d));
  const counts = {};
  DATA.events.forEach(e => { const k = e.start.slice(0, 10); counts[k] = (counts[k] || 0) + 1; });

  const strip = document.getElementById('day-strip');
  const list = document.getElementById('list');
  const label = document.getElementById('day-label');
  const title = document.getElementById('day-title');
  const sub = document.getElementById('day-sub');

  function renderStrip(selected) {
    let lastMonth = null;
    strip.innerHTML = days.map(iso => {
      const d = parseDay(iso);
      const n = counts[iso] || 0;
      const weekend = d.getDay() === 0 || d.getDay() === 6;
      const name = iso === todayISO ? 'Heute' : iso === tomorrowISO ? 'Morgen' : WD_SHORT[d.getDay()];
      let month = '';
      if (lastMonth !== null && d.getMonth() !== lastMonth) {
        month = `<span class="strip-month" aria-hidden="true">${MONTHS[d.getMonth()]}</span>`;
      }
      lastMonth = d.getMonth();
      return `${month}<button type="button" class="day${weekend ? ' is-weekend' : ''}${n ? '' : ' is-empty'}"
          data-day="${iso}" aria-pressed="${iso === selected}"
          aria-label="${longDate(d)}: ${n} ${n === 1 ? 'Heuriger' : 'Heurige'}">
          <span class="day-name">${name}</span>
          <span class="day-date">${shortDate(d)}</span>
          <span class="day-count">${n}</span>
        </button>`;
    }).join('');
    const active = strip.querySelector('[aria-pressed="true"]');
    if (active) strip.scrollLeft = active.offsetLeft - strip.clientWidth / 2 + active.clientWidth / 2;
  }

  function renderDay(iso, push) {
    if (!days.includes(iso)) iso = todayISO;
    const d = parseDay(iso);
    let events = eventsOn(iso);
    let states = events.map(e => status(e, iso));

    // Today: open now first, then opening later, then already closed
    if (iso === todayISO) {
      const order = events.map((e, i) => i).sort((a, b) => states[a].order - states[b].order || a - b);
      events = order.map(i => events[i]);
      states = order.map(i => states[i]);
    }

    const n = events.length;
    const rel = relativeDay(iso);
    label.textContent = (rel === 'Heute' || rel === 'Morgen') ? `${rel} · ${longDate(d)}` : longDate(d);

    if (n === 0) {
      title.textContent = iso === todayISO ? "Heute hat kein Heuriger ausg'steckt" : "Kein Heuriger hat ausg'steckt";
    } else {
      const when = iso === todayISO ? 'heute ' : iso === tomorrowISO ? 'morgen ' : '';
      title.textContent = n === 1 ? `1 Heuriger hat ${when}ausg'steckt` : `${n} Heurige haben ${when}ausg'steckt`;
    }

    sub.innerHTML = '';
    if (iso === todayISO && n > 0) {
      const open = states.filter(s => s.cls === 'open').length;
      const firstSoon = states.findIndex(s => s.cls === 'soon');
      if (open > 0) {
        const text = open === n ? (n === 1 ? 'Hat jetzt offen' : 'Alle haben jetzt offen')
          : `${open} davon ${open === 1 ? 'hat' : 'haben'} jetzt offen`;
        sub.innerHTML = `<span class="live-dot" aria-hidden="true"></span>${text}`;
      } else if (firstSoon >= 0) {
        sub.textContent = `Der erste sperrt um ${time(events[firstSoon].start)} Uhr auf`;
      } else {
        sub.textContent = 'Für heute haben alle schon zugesperrt.';
      }
    }
    if (n === 0) {
      const next = days.find(x => x > iso && counts[x]);
      if (next) {
        const nd = parseDay(next);
        sub.innerHTML = `<button type="button" class="link-btn" data-day="${next}">Nächster Tag mit offenen Heurigen: ${relativeDay(next)}, ${shortDate(nd)} →</button>`;
      }
    }

    list.innerHTML = events.map((e, i) => cardHTML(e, i, states[i])).join('');
    list.hidden = n === 0;
    document.querySelector('.layout').classList.toggle('is-empty', n === 0);
    renderMap(events, states);
    renderStrip(iso);

    // Shareable link per day (today = plain URL)
    if (push) history.replaceState(null, '', iso === todayISO ? location.pathname : `#${iso}`);
  }

  function renderAll() {
    const ul = document.getElementById('all-list');
    if (!ul) return;
    ul.innerHTML = DATA.heurigen.map(h => {
      const next = DATA.events.find(e => {
        if (e.title !== h.title) return false;
        const iso = e.start.slice(0, 10);
        if (iso > todayISO) return true;
        if (iso < todayISO) return false;
        const st = status(e, iso);
        return st.cls !== 'closed';
      });
      let when = '<span class="all-none">derzeit keine Termine bekannt</span>';
      if (next) {
        const iso = next.start.slice(0, 10);
        const d = parseDay(iso);
        const st = status(next, iso);
        const from = `ab ${time(next.start)}`;
        const rel = iso === todayISO ? (st.cls === 'open' ? 'jetzt offen' : `heute ${from}`)
          : iso === tomorrowISO ? `morgen ${from}`
            : `${WD_SHORT[d.getDay()]}, ${shortDate(d)} ${from}`;
        when = `<button type="button" class="all-next${iso === todayISO ? ' is-today' : ''}" data-day="${iso}">${rel}</button>`;
      }
      const name = `<a href="${esc(h.page)}">${esc(h.title)}</a>`;
      return `<li><span class="all-name">${name}</span>${when}</li>`;
    }).join('');
  }

  // Any element with data-day selects that day
  document.addEventListener('click', ev => {
    const btn = ev.target.closest('[data-day]');
    if (!btn) return;
    renderDay(btn.dataset.day, true);
    if (!btn.closest('#day-strip')) {
      document.querySelector('.answer').scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
  });

  bindList();
  const initial = location.hash.slice(1);
  renderDay(/^\d{4}-\d{2}-\d{2}$/.test(initial) ? initial : todayISO, false);
  renderAll();
})();
