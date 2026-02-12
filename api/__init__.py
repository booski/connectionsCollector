from datetime import date, timedelta
import random
import re

from flask import Flask, g, request
import requests

from .db import get_db, evolve

app = Flask('connections')
evolve(get_db())


class ValidationException(Exception):
    pass


def get_today(db, now):
    result = db.execute(
        'SELECT `id`, `author` FROM `puzzles` WHERE `date`=?', (now,)).fetchone()
    if result:
        return result

    result = db.execute(
        'SELECT `id`, `author`FROM `puzzles` WHERE `date` ISNULL').fetchall()
    selected = random.choice([row['id'] for row in result])
    db.execute('UPDATE `puzzles` SET `date`=? WHERE `id`=?',
               (now, selected))
    db.commit()
    return get_today(db, now)


def get_author(puzzle_id):
    result = requests.get(
        f'https://connections.swellgarfo.com/game/{puzzle_id}')
    if result.status_code != 200:
        raise ValidationException()

    author = None
    author_match = re.search(r'"author":"([^"]*)"', result.text)
    if author_match:
        author = author_match.group(1)
    return author


@app.before_request
def before():
    if 'db' not in g:
        g.db = get_db()


@app.route('/today')
def get_puzzle_data():
    now = date.today().isoformat()
    today_result = get_today(g.db, now)
    older_result = g.db.execute(
        'SELECT `date`, `id` FROM `puzzles` WHERE `date`<?', (now,)).fetchall()
    coming_result = g.db.execute(
        'SELECT `id` FROM `puzzles` WHERE `date` ISNULL').fetchall()

    if today_result:
        today_item = {'id': today_result['id'],
                      'author': today_result['author']}
        if not today_item['author']:
            # Fallback for old puzzles lacking stored author
            today_item['author'] = get_author(today_item['id'])
    else:
        today_item = {'id': None,
                      'author': None}

    if not older_result:
        older_result = []
    if not coming_result:
        coming_result = []

    return {'today': today_item,
            'older': [{'date': row['date'],
                       'id': row['id']}
                      for row in older_result],
            'coming': len(coming_result)}


@app.route('/submit', methods=['PUT'])
def submit_puzzle():
    puzzle_id = request.json['id']

    try:
        author = get_author(puzzle_id)
    except ValidationException:
        return {'result': 'error'}
        
    g.db.execute('INSERT INTO `puzzles` (`id`, `author`) VALUES (?, ?)',
                 (puzzle_id, author))
    g.db.commit()
    return {'result': 'ok'}
