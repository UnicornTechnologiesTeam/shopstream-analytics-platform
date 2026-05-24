from flask import Flask, jsonify, request
import psycopg2
import os

app = Flask(__name__)

DB_HOST = "shopstream-dw.cc9uttu2shgi.us-east-1.rds.amazonaws.com"
DB_NAME = "shopstream_dw"
DB_USER = "postgres"
DB_PASS = "shopstream1234"

def get_conn():
    return psycopg2.connect(
        host=DB_HOST, dbname=DB_NAME,
        user=DB_USER, password=DB_PASS
    )

@app.route('/pages/top')
def pages_top():
    metric = request.args.get('metric', 'time_on_page')
    limit  = int(request.args.get('limit', 10))

    if metric == 'bounce_rate':
        q = f"SELECT page_type, bounce_rate FROM bounce_rate ORDER BY bounce_rate DESC LIMIT {limit}"
    else:
        q = f"SELECT page_url, avg_time_seconds, visits FROM top_pages ORDER BY avg_time_seconds DESC LIMIT {limit}"

    conn = get_conn()
    cur  = conn.cursor()
    cur.execute(q)
    cols = [d[0] for d in cur.description]
    rows = [dict(zip(cols, r)) for r in cur.fetchall()]
    conn.close()
    return jsonify({'metric': metric, 'data': rows})

@app.route('/sessions/summary')
def sessions_summary():
    country = request.args.get('country')
    device  = request.args.get('device')

    q      = "SELECT device_type, country, avg_time_seconds, sessions FROM device_country WHERE 1=1"
    params = []
    if country:
        q += " AND country = %s"
        params.append(country)
    if device:
        q += " AND device_type = %s"
        params.append(device)
    q += " ORDER BY sessions DESC"

    conn = get_conn()
    cur  = conn.cursor()
    cur.execute(q, params)
    cols = [d[0] for d in cur.description]
    rows = [dict(zip(cols, r)) for r in cur.fetchall()]
    conn.close()
    return jsonify({'data': rows})

@app.route('/anomalies')
def anomalies():
    date   = request.args.get('date')
    q      = "SELECT session_id, user_id, page_url, time_on_page_seconds, z_score FROM anomalies"
    params = []
    if date:
        q += " WHERE event_date = %s"
        params.append(date)
    q += " ORDER BY z_score DESC LIMIT 100"

    conn = get_conn()
    cur  = conn.cursor()
    cur.execute(q, params)
    cols = [d[0] for d in cur.description]
    rows = [dict(zip(cols, r)) for r in cur.fetchall()]
    conn.close()
    return jsonify({'anomalies': rows, 'count': len(rows)})

if __name__ == '__main__':
    app.run(debug=True)
