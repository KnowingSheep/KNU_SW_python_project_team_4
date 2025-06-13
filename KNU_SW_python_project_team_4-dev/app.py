from flask import Flask, abort, render_template, jsonify, request
from sqlalchemy import create_engine, text
import pandas as pd

def parse_year():
    year = request.args.get('year')
    if not year:
        abort(400, description="'year' parameter required")
    try:
        return int(year)
    except ValueError:
        abort(400, description="'year' must be an integer")

app = Flask(__name__)

DB_URL = "postgresql+psycopg2://postgres:1356@192.168.0.6:5432/team4db"
engine = create_engine(DB_URL)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/years')
def api_years():
    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT DISTINCT EXTRACT(YEAR FROM datetime) AS year
            FROM accidents
            ORDER BY year
        """))
        years = [int(row.year) for row in result]
    return jsonify(years)

@app.route('/api/provinces')
def api_provinces():
    year = request.args.get('year')
    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT p.province, p.lng, p.lat
            FROM provinces p
            WHERE EXISTS (
                SELECT 1 FROM accidents a
                WHERE EXTRACT(YEAR FROM a.datetime) = :year
                AND a.province = p.province
            )
        """), {"year": year})
        rows = [dict(row._mapping) for row in result]
    return jsonify(rows)


@app.route('/api/cities')
def api_cities():
    year = request.args.get('year')
    province = request.args.get('province')
    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT d.city, d.lng, d.lat
            FROM districts d
            WHERE d.province = :province AND EXISTS (
                SELECT 1 FROM accidents a
                WHERE EXTRACT(YEAR FROM a.datetime) = :year
                  AND a.province = d.province
                  AND a.city = d.city
            )
        """), {"year": year, "province": province})
        rows = [dict(row._mapping) for row in result]
    return jsonify(rows)


@app.route('/api/accidents')
def api_accidents():
    year = parse_year()
    province = request.args.get('province')
    city = request.args.get('city')

    if not province or not city:
        abort(400, description="'province' and 'city' parameters are required")

    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT id, lat, lng,
                   to_char(datetime, 'YYYY-MM-DD') AS date,
                   CONCAT(type_desc, ' - ', law_violation) AS desc,
                   type_major
            FROM accidents
            WHERE EXTRACT(YEAR FROM datetime) = :year
              AND province = :province
              AND city = :city
        """), {"year": year, "province": province, "city": city})
        rows = [dict(row._mapping) for row in result]
    return jsonify(rows)


@app.route("/statistics")
def show_statistics():
    return render_template("statistics.html")

@app.route("/api/statistics")
def api_statistics():
    year = request.args.get("year")
    city = request.args.get("city")

    query = "SELECT datetime, city FROM accidents WHERE datetime IS NOT NULL"
    filters = []

    if year:
        filters.append(f"EXTRACT(YEAR FROM datetime) = {int(year)}")
    if city:
        filters.append(f"city = :city")

    if filters:
        query += " AND " + " AND ".join(filters)

    # 파라미터 바인딩용 딕셔너리
    params = {}
    if city:
        params["city"] = city

    df = pd.read_sql(text(query), engine, params=params)

    if df.empty:
        return jsonify({
            "weekdays": [], "weekday_counts": [],
            "hours": [], "hour_counts": [],
            "cities": [], "city_counts": []
        })

    df['weekday'] = pd.to_datetime(df['datetime']).dt.day_name()
    weekday_counts = df['weekday'].value_counts().reindex(
        ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    ).fillna(0)

    df['hour'] = pd.to_datetime(df['datetime']).dt.hour
    hour_counts = df['hour'].value_counts().sort_index()

    city_counts = df['city'].value_counts().head(10)

    return jsonify({
        "weekdays": weekday_counts.index.tolist(),
        "weekday_counts": weekday_counts.values.tolist(),
        "hours": hour_counts.index.tolist(),
        "hour_counts": hour_counts.values.tolist(),
        "cities": city_counts.index.tolist(),
        "city_counts": city_counts.values.tolist()
    })



if __name__ == '__main__':
    app.run(debug=True)
