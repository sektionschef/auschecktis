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
                color: '#28a745',
                textColor: 'white'
            },
            {
                url: 'data/barthuette.json',
                color: '#007bff',
                textColor: 'white'
            },
            {
                url: 'data/biohof_nummer_5.json',
                color: '#007bff',
                textColor: 'white'
            },
            {
                url: 'data/goebel.json',
                color: '#007bff',
                textColor: 'white'
            },
            {
                url: 'data/presshaus.json',
                color: '#007bff',
                textColor: 'white'
            },
            {
                url: 'data/wieninger.json',
                color: '#007bff',
                textColor: 'white'
            },
            {
                url: 'data/lentner_koarl.json',
                color: '#007bff',
                textColor: 'white'
            }

        ]
    });

    calendar.render();
});
