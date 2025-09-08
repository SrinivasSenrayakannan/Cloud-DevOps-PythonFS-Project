import os, tempfile, json
import app as app_module

def test_health():
    app = app_module.app
    client = app.test_client()
    rv = client.get('/health')
    assert rv.status_code == 200
    assert rv.get_json()['status'] == 'ok'

def test_index():
    # Use a temp DB for tests
    db_fd, db_path = tempfile.mkstemp()
    os.environ['DB_PATH'] = db_path
    app = app_module.app
    with app.app_context():
        app_module.init_db()
    client = app.test_client()
    assert client.get('/').status_code == 200
