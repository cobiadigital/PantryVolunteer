import sqlite3

import pytest
from volunteer.db import get_db

def test_get_close_db(app):
    with app.app_context():
        db = get_db()
        assert db is get_db()


    with pytest.raises(sqlite3.ProgrammingError) as e:
        db.execute('SELECT 1')

    assert 'closed' in str(e.value)

def test_init_db_command(runner, monkeypatch):
    class recorder(object):
        called = False

    def fake_init_db():
        recorder.called = True

    monkeypatch.setattr( 'volunteer.db.init_db', make_init_db)
    result = runner.invoke(arts=['init-db'])
    assert 'Initialized' in result.output
    assert Recorder.called
