from datetime import date, timedelta
import json
import random
import re

from bs4 import BeautifulSoup
from flask import Flask, g, request
import requests

from .db import get_db, evolve

app = Flask('connections')
evolve(get_db())


class ValidationException(Exception):
    pass


def fix_old_puzzle(db, puzzle_id):
    # This is a puzzle submitted before author and/or title were
    # being stored in the database, update it
    title, author = get_info(puzzle_id)
    db.execute('UPDATE `puzzles` SET `author`=?, `title`=? WHERE `id`=?',
               (author, title, puzzle_id))
    db.commit()
    result = db.execute('SELECT `id`, `author`, `title`, `date` '
                        'FROM `puzzles` WHERE `id`=?', (puzzle_id,)).fetchone()
    return {'id': result['id'],
            'author': result['author'],
            'title': result['title'],
            'date': result['date']}


def get_previous(db, now):
    result = g.db.execute('SELECT `date`, `id`, `author`, `title` '
                          'FROM `puzzles` WHERE `date`<?',
                          (now,)).fetchall()
    items = []
    for row in result:
        if row['title'] is None or row['author'] is None:
            items.append(fix_old_puzzle(db, row['id']))
            continue
        items.append({'id': row['id'],
                      'author': row['author'],
                      'title': row['title'],
                      'date': row['date']})
    return items


def get_today(db, now):
    result = db.execute('SELECT `id`, `author`, `title` '
                        'FROM `puzzles` WHERE `date`=?', (now,)).fetchone()
    if result:
        if result['title'] is not None and result['author'] is not None:
            return {'id': result['id'],
                    'author': result['author'],
                    'title': result['title']}
        return fix_old_puzzle(db, result['id'])


    # No puzzle assigned for today
    result = db.execute(
        'SELECT `id` FROM `puzzles` WHERE `date` ISNULL').fetchall()
    if not result:
        # There are no new puzzles
        return {'id': None,
                'author': None,
                'title': None}

    # Randomize a new one and store it
    selected = random.choice([row['id'] for row in result])
    db.execute('UPDATE `puzzles` SET `date`=? WHERE `id`=?',
               (now, selected))
    db.commit()
    return get_today(db, now)


def get_info(puzzle_id):
    result = requests.get(
        f'https://connections.swellgarfo.com/game/{puzzle_id}')
    if result.status_code != 200:
        raise ValidationException()

    soup = BeautifulSoup(result.text, 'html.parser')
    puzzledata = json.loads(soup.find(id='__NEXT_DATA__').string)
    metadata = puzzledata['props']['pageProps']['puzzleMetadata']
    return (metadata['title'], metadata['author'])


@app.before_request
def before():
    if 'db' not in g:
        g.db = get_db()


@app.route('/today')
def get_puzzle_data():
    now = date.today().isoformat()
    older_result = g.db.execute('SELECT `date`, `id`, `author`, `title` '
                                'FROM `puzzles` WHERE `date`<?',
                                (now,)).fetchall()
    coming_result = g.db.execute(
        'SELECT `id` FROM `puzzles` WHERE `date` ISNULL').fetchall()

    if not older_result:
        older_result = []
    if not coming_result:
        coming_result = []

    return {'today': get_today(g.db, now),
            'older': get_previous(g.db, now),
            'coming': len(coming_result)}


@app.route('/submit', methods=['PUT'])
def submit_puzzle():
    puzzle_id = request.json['id']

    try:
        title, author = get_info(puzzle_id)
    except Exception:
        return {'result': 'error'}
        
    g.db.execute('INSERT INTO `puzzles` (`id`, `author`, `title`) '
                 'VALUES (?, ?, ?)',
                 (puzzle_id, author, title))
    g.db.commit()
    return {'result': 'ok'}
