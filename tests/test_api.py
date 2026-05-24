import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from unittest.mock import patch, MagicMock
from app import app
import json

def get_client():
    app.config['TESTING'] = True
    return app.test_client()

def mock_conn(rows, cols):
    cur = MagicMock()
    cur.description = [(c,) for c in cols]
    cur.fetchall.return_value = rows
    conn = MagicMock()
    conn.cursor.return_value = cur
    return conn

@patch('app.get_conn')
def test_pages_top_time(mock_get_conn):
    mock_get_conn.return_value = mock_conn(
        [('/home/best-sellers', 120.5, 1000)],
        ['page_url', 'avg_time_seconds', 'visits']
    )
    client = get_client()
    r = client.get('/pages/top?metric=time_on_page&limit=5')
    assert r.status_code == 200
    data = json.loads(r.data)
    assert 'data' in data
    assert data['data'][0]['page_url'] == '/home/best-sellers'

@patch('app.get_conn')
def test_pages_top_bounce(mock_get_conn):
    mock_get_conn.return_value = mock_conn(
        [('home', 0.45)],
        ['page_type', 'bounce_rate']
    )
    client = get_client()
    r = client.get('/pages/top?metric=bounce_rate&limit=5')
    assert r.status_code == 200
    data = json.loads(r.data)
    assert data['metric'] == 'bounce_rate'

@patch('app.get_conn')
def test_sessions_summary(mock_get_conn):
    mock_get_conn.return_value = mock_conn(
        [('mobile', 'CO', 89.5, 40263)],
        ['device_type', 'country', 'avg_time_seconds', 'sessions']
    )
    client = get_client()
    r = client.get('/sessions/summary?country=CO&device=mobile')
    assert r.status_code == 200
    data = json.loads(r.data)
    assert data['data'][0]['country'] == 'CO'

@patch('app.get_conn')
def test_anomalies(mock_get_conn):
    mock_get_conn.return_value = mock_conn(
        [('s1', 'u1', '/home', 900, 4.2)],
        ['session_id', 'user_id', 'page_url', 'time_on_page_seconds', 'z_score']
    )
    client = get_client()
    r = client.get('/anomalies?date=2026-05-21')
    assert r.status_code == 200
    data = json.loads(r.data)
    assert data['count'] == 1
    assert data['anomalies'][0]['z_score'] == 4.2

@patch('app.get_conn')
def test_anomalies_sin_fecha(mock_get_conn):
    mock_get_conn.return_value = mock_conn(
        [('s1', 'u1', '/home', 900, 4.2)],
        ['session_id', 'user_id', 'page_url', 'time_on_page_seconds', 'z_score']
    )
    client = get_client()
    r = client.get('/anomalies')
    assert r.status_code == 200