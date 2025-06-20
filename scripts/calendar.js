

document.addEventListener('DOMContentLoaded', function () {
    const calendarEl = document.getElementById('calendar');

    const calendar = new FullCalendar.Calendar(calendarEl, {
        themeSystem: 'bootstrap5',
        initialView: 'listDay',
        firstDay: 1, // Montag
        locale: 'de',
        timeZone: 'Europe/Vienna',
        headerToolbar: {
            left: 'prev,next today',
            center: 'title',
            right: 'listDay,listWeek'
        },
        buttonText: {
            listDay: 'Tag',
            listWeek: 'Woche',
            today: "heute",
        },
        views: {
            listDay: {
                // titleFormat: { weekday: 'short', month: 'short', day: 'numeric' }
                titleFormat: { month: 'short', day: 'numeric' }
            },
            listWeek: {
                titleFormat: { month: 'short', day: 'numeric' }
            }
        },
        /* ➊  Kalender soll so hoch sein wie der Inhalt  */
        height: 'auto',          // oder contentHeight: 'auto'
        handleWindowResize: true, // wächst mit, wenn Fenster größer/kleiner wird
        eventSources: [
            {
                url: 'data/almdudler_standl.json',
                // color: '#a72828',
                // textColor: 'white'
            },
            {
                url: 'data/barthuette.json',
                // color: '#00ffff',
                // textColor: 'white'
            },
            {
                url: 'data/biohof_nummer_5.json',
                // color: '#236415',
                // textColor: 'white'
            },
            {
                url: 'data/goebel.json',
                // color: '#181447',
                // textColor: 'white'
            },
            {
                url: 'data/presshaus.json',
                // color: '#007bff',
                // textColor: 'white'
            },
            {
                url: 'data/wieninger.json',
                // color: '#3e5a3e',
                // textColor: 'white'
            },
            {
                url: 'data/lentner_koarl.json',
                // color: '#f3a641',
                // textColor: 'white'
            },
            {
                url: 'data/leopold.json',
                // color: '#f3a641',
                // textColor: 'white'
            },
            {
                url: 'data/helm.json',
                // color: '#f3a641',
                // textColor: 'white'
            },
            {
                url: 'data/reinbacher.json',
                // color: '#f3a641',
                // textColor: 'white'
            },
            {
                url: 'data/klager.json',
                // color: '#f3a641',
                // textColor: 'white'
            },
            {
                url: 'data/dornroeschenkeller.json',
                // color: '#f3a641',
                // textColor: 'white'
            },
            {
                url: 'data/duschl.json',
                // color: '#f3a641',
                // textColor: 'white'
            },
            {
                url: 'data/gustl.json',
                // color: '#f3a641',
                // textColor: 'white'
            },
            {
                url: 'data/kammerer.json',
                // color: '#f3a641',
                // textColor: 'white'
            },
            {
                url: 'data/weinhandwerk.json',
                // color: '#f3a641',
                // textColor: 'white'
            },
            {
                url: 'data/walter.json',
                // color: '#f3a641',
                // textColor: 'white'
            },
            {
                url: 'data/ausblick_wien.json',
                // color: '#f3a641',
                // textColor: 'white'
            },
            {
                url: 'data/christl.json',
                // color: '#f3a641',
                // textColor: 'white'
            }
        ],

        eventDidMount: function (info) {
            // Only apply to list view events
            if (info.view.type.startsWith('list')) {
                const { mapLink } = info.event.extendedProps;

                if (mapLink) {
                    const button = document.createElement('a');
                    button.href = mapLink;
                    button.textContent = 'Map';
                    button.target = '_blank';
                    button.rel = 'noopener noreferrer';
                    // button.className = 'btn btn-sm btn-outline-secondary ms-2';
                    button.className = 'btn btn-sm btn-outline-secondary ms-2';

                    // 🛡 prevent event row click from hijacking the button
                    button.addEventListener('click', function (ev) {
                        ev.stopPropagation();
                    });

                    const titleEl = info.el.querySelector('.fc-list-event-title');
                    if (titleEl) {
                        titleEl.appendChild(button);
                    }
                }
            }
        }
    });

    calendar.render();
});
