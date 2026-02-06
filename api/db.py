import sqlite3
from pathlib import Path
import os


sqlite3.register_converter(
    "timestamp", lambda v: datetime.fromisoformat(v.decode()))

def evolve(db):
    print('Evolving database')
    # Bootstrap by initializing the evolutions table if it doesn't exist.
    db.executescript('''
    CREATE TABLE IF NOT EXISTS `evolutions` (
    `filename` TEXT PRIMARY KEY,
    `apply_date` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
    );''')
    db.commit()

    applied = {row['filename'] for row
               in db.execute('select `filename` from `evolutions`').fetchall()}
    available = Path('./evolutions').glob('*.sql')

    for sqlfile in available:
        filename = sqlfile.name
        if filename not in applied:
            print(f'Applying {filename}')
            with open(sqlfile, 'r') as f:
                db.executescript(f.read())
            db.execute('insert into `evolutions` (`filename`) values (?)',
                       (filename,))
            db.commit()
        else:
            print(f'Skipping {filename}, already applied')

    print('Database evolution done')


def get_db():
    base = Path(os.path.dirname(__file__)).parent
    db = sqlite3.connect(base / 'db/data.sqlite',
                         detect_types=sqlite3.PARSE_DECLTYPES)
    db.row_factory = sqlite3.Row

    return db
