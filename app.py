from flask import Flask, abort, render_template, jsonify, request
from sqlalchemy import create_engine, text

def parse_year():
    year = request.args.get('year')
    if not year:
        abort(400, description="'year' parameter required")
    try:
        return int(year)
    except ValueError:
        abort(400, description="'year' must be an integer")

app = Flask(__name__)

DB_URL = "postgresql+psycopg2://postgres:1356@25.50.71.151:5432/team4db"
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


if __name__ == '__main__':
    app.run(debug=True)
