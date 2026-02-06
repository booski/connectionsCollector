from datetime import date, timedelta

from flask import Flask, g, request
import requests

from .db import get_db, evolve

app = Flask('connections')
evolve(get_db())


@app.before_request
def before():
    if db not in g:
        g.db = get_db()

@app.route('/today')
def get_puzzle_data():
    now = date.today().isoformat()
    today_result = g.db.execute('SELECT `id` FROM `puzzles` WHERE `date`==?',
                                (now,)).fetchone()
    older_result = g.db.execute('SELECT `date`, `id` FROM `puzzles` WHERE `date`<?',
                                (now,)).fetchall()
    coming_result = g.db.execute('SELECT `date` FROM `puzzles` WHERE `date`>?',
                                 (now,)).fetchall()
    if not coming_result:
        coming_result = []
    return {'today': today_result['id'],
            'older': [{'date': row['date'],
                       'id': row['id']}
                      for row in older_result],
            'coming': len(coming_result)}

@app.route('/submit', methods=['PUT'])
def submit_puzzle():
    puzzle_id = request.json['id']
    now = date.today()
    result = requests.get(
        f'https://connections.swellgarfo.com/game/{puzzle_id}')
    if result.status_code == 200:
        result_row = g.db.execute(
            'SELECT max(`date`) as `date` from `puzzles`').fetchone()
        last_date = date.fromisoformat(result_row['date'])
        if last_date < now:
            next_date = now
        else:
            next_date = last_date + timedelta(days=1)
        g.db.execute('INSERT INTO `puzzles` (`id`, `date`) VALUES (?, ?)',
                     (puzzle_id, next_date.isoformat()))
        g.db.commit()
        return {'result': 'ok'}
    return {'result': 'error'}
