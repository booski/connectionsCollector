'use strict';

const swellgarfo = 'https://connections.swellgarfo.com/game/';

window.addEventListener('DOMContentLoaded', async (event) => {
    makeRequest('GET', '/today', null)
        .then((data) => {
            configureLink(document.getElementById('today-link'), data.today);
            setHistory(data.older);
        });
});

function configureLink(linkElem, id) {
    const link = swellgarfo + id;
    linkElem.setAttribute('href', link);
    linkElem.textContent = link;
}

function setHistory(itemList) {
    const itemTemplate = document.getElementById('archive-item');
    const itemListElem = document.getElementById('archive-list');

    for(const item of itemList) {
        const itemElem = itemTemplate.content.cloneNode(true);
        itemElem.querySelector('.date').textContent = item.date;
        configureLink(itemElem.querySelector('.link'), item.id);
        itemListElem.appendChild(itemElem);
    }
}

async function makeRequest(method, path, body) {
    const data = {'method': method,
                  'headers': {'Content-Type': 'application/json'}};

    if(method != 'GET') {
        data['body'] = JSON.stringify(body);
    }
    const request = new Request('/api' + path, data);
    return fetch(request)
        .then((response) => {
            return response.json();
        }, (error) => {
            alert('A network error has occurred. Please reload the page.');
        });
}
