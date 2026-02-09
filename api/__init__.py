from datetime import date, timedelta

from flask import Flask, g, request
import requests
import random

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
        result_rows = g.db.execute(
            'SELECT `id`, `date` from `puzzles` WHERE `date` > ? ORDER BY `date` DESC', (now.isoformat(),)).fetchall()
        if(len(result_rows) > 0):
            next_date = date.fromisoformat(result_rows[0]['date']) + timedelta(days=1)
        else:
            next_date = now

        all_dates = list(map(lambda row: date.fromisoformat(row['date']), result_rows))
        all_dates.append(next_date)
        random.shuffle(all_dates)
        
        new_date = all_dates[len(all_dates) - 1]

        # clear out all dates with dummy values to stop the unique constraint from getting in the way
        for i in range(len(result_rows)):
            g.db.execute('UPDATE `puzzles` SET `date`=? WHERE `id`=?',
                         ((date.fromisoformat('8888-12-31') + timedelta(days=i)).isoformat(), result_rows[i]['id']))

        for i in range(len(result_rows)):
            sql = 'UPDATE `puzzles` SET `date`=? WHERE `id`=?'
            g.db.execute(sql, (all_dates[i].isoformat(), result_rows[i]['id']))

        g.db.execute('INSERT INTO `puzzles` (`id`, `date`) VALUES (?, ?)',
                     (puzzle_id, new_date.isoformat()))
        g.db.commit()
        return {'result': 'ok'}
    return {'result': 'error'}
