'use strict';

const swellgarfo = 'https://connections.swellgarfo.com/game/';

window.addEventListener('DOMContentLoaded', async (event) => {
    updatePage();
    document.getElementById('submit').addEventListener('submit', (event) => {
        event.preventDefault();
        makeRequest('PUT',
                    '/submit',
                    {'id': document.getElementById('submit-field').value})
            .then((data) => {
                const resultElem = document.getElementById('result');
                if(data.result == 'ok') {
                    resultElem.classList.remove('error');
                    resultElem.classList.add('success');
                    resultElem.textContent = 'Thank you!';
                } else {
                    resultElem.classList.add('error');
                    resultElem.classList.remove('success');
                    resultElem.textContent = 'Error, try again?';
                }
                setTimeout(() => {
                    resultElem.textContent = '';
                }, 5000);
                updatePage();
            });
    });
});

async function updatePage() {
    makeRequest('GET', '/today', null)
        .then((data) => {
            setToday(data.today);
            document.getElementById('upcoming').textContent = data.coming;
            setHistory(data.older);
        });
}

function configureLink(linkElem, id) {
    const link = swellgarfo + id;
    linkElem.setAttribute('href', link);
    linkElem.textContent = link;
}

function setToday(todayItem) {
    if(!todayItem.id) {
        return;
    }

    const todayElem = document.getElementById('today-link');
    const linkTemplate = document.getElementById('today-template');
    const newLink = document.createElement('a');
    newLink.setAttribute('id', 'today-link');

    configureLink(newLink, todayItem.id);
    todayElem.replaceWith(newLink);

    const authorElem = document.getElementById('author');
    if(todayItem.author) {
        authorElem.textContent = todayItem.author;
    } else {
        authorElem.parentNode.removeChild(authorElem);
    }
}

function setHistory(itemList) {
    const itemTemplate = document.getElementById('archive-item');
    const itemListElem = document.getElementById('archive-list');

    if(itemList.length == 0) {
        itemListElem.replaceWith('No old puzzles available');
        return;
    }

    itemListElem.innerHTML = '';
    const sortedList = itemList.sort((a, b) => {
        if (a.date < b.date) {
            return 1;
        }
        return -1;
    });
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
