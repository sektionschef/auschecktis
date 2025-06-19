document.addEventListener('DOMContentLoaded', function () {
    const calendarEl = document.getElementById('calendar');

    const calendar = new FullCalendar.Calendar(calendarEl, {
        initialView: 'listDay',
        firstDay: 1, // Montag
        locale: 'de',
        timeZone: 'Europe/Vienna',
        headerToolbar: {
            left: 'prev,next today',
            center: 'title',
            right: 'timeGridWeek,listWeek'
        },
        eventSources: [
            {
                url: 'data/almdudler_standl.json',
                color: '#a72828',
                textColor: 'white'
            },
            {
                url: 'data/barthuette.json',
                color: '#00ffff',
                textColor: 'white'
            },
            {
                url: 'data/biohof_nummer_5.json',
                color: '#236415',
                textColor: 'white'
            },
            {
                url: 'data/goebel.json',
                color: '#181447',
                textColor: 'white'
            },
            {
                url: 'data/presshaus.json',
                color: '#007bff',
                textColor: 'white'
            },
            {
                url: 'data/wieninger.json',
                color: '#3e5a3e',
                textColor: 'white'
            },
            {
                url: 'data/lentner_koarl.json',
                color: '#f3a641',
                textColor: 'white'
            }

        ]
    });

    calendar.render();
});
