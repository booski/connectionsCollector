from datetime import date, timedelta

from flask import Flask, g
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
    today = date.today().isoformat()
    return {'today': g.db.execute('SELECT `id` FROM `puzzles` WHERE `date`==?',
                                  (today,)).fetchone(),
            'older': g.db.execute('SELECT `id` FROM `puzzles` WHERE `date`<?',
                                  (today,)).fetchall(),
            'coming': len(g.db.execute('SELECT `id`FROM `puzzles` WHERE `date`>?',
                                     (today,)).fetchall())}

@app.route('/submit/<puzzle_id>', methods=['PUT'])
def submit_puzzle(puzzle_id):
    result = requests.get(
        f'https://connections.swellgarfo.com/game/{puzzle_id}')
    if result.status_code == 200:
        last_date = d.db.execute(
            'SELECT `date` max(`date`) from `puzzles`').fetchone()
        last_date = date.fromisoformat(last_date)
        next_date = last_date + timedelta(days=1)
        g.db.execute('INSERT INTO `puzzles` (`id`, `date`) VALUES (?, ?)',
                     puzzle_id, next_date.isoformat())
        g.db.commit()
    return {'result': 'ok'}
