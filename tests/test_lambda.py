import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from lambda_function import validate_record

def test_page_view_valido():
    rec = {
        "event_type": "page_view",
        "user_id": "u1",
        "session_id": "s1",
        "page_url": "/home",
        "page_type": "home",
        "timestamp": "2026-05-21T10:00:00",
        "time_on_page_seconds": 30,
        "device_type": "mobile",
        "country": "CO",
        "referrer": "https://google.com"
    }
    ok, msg = validate_record(rec)
    assert ok is True

def test_page_view_falta_campo():
    rec = {"event_type": "page_view", "user_id": "u1", "session_id": "s1"}
    ok, msg = validate_record(rec)
    assert ok is False
    assert "obligatorio" in msg

def test_event_type_desconocido():
    rec = {"event_type": "unknown", "user_id": "u1"}
    ok, msg = validate_record(rec)
    assert ok is False
    assert "desconocido" in msg

def test_timestamp_invalido():
    rec = {
        "event_type": "search",
        "user_id": "u1",
        "session_id": "s1",
        "query": "test",
        "results_count": 5,
        "timestamp": "no-es-fecha"
    }
    ok, msg = validate_record(rec)
    assert ok is False
    assert "timestamp" in msg

def test_cart_event_valido():
    rec = {
        "event_type": "cart_event",
        "user_id": "u1",
        "session_id": "s1",
        "product_id": "P0001",
        "action": "add",
        "timestamp": "2026-05-21T12:00:00"
    }
    ok, msg = validate_record(rec)
    assert ok is True

def test_product_view_valido():
    rec = {
        "event_type": "product_view",
        "user_id": "u1",
        "session_id": "s1",
        "product_id": "P0001",
        "category": "electronics",
        "price": 99.99,
        "timestamp": "2026-05-21T12:00:00",
        "time_on_page_seconds": 45
    }
    ok, msg = validate_record(rec)
    assert ok is True

def test_click_valido():
    rec = {
        "event_type": "click",
        "user_id": "u1",
        "session_id": "s1",
        "element_id": "btn001",
        "element_type": "button",
        "page_url": "/home",
        "timestamp": "2026-05-21T12:00:00",
        "x_position": 100,
        "y_position": 200
    }
    ok, msg = validate_record(rec)
    assert ok is True
