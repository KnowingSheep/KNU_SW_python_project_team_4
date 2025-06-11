from flask import Flask, render_template, jsonify, request
from sqlalchemy import create_engine, text

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
            SELECT province, ST_X(ST_Centroid(ST_Collect(geom))) AS lng, ST_Y(ST_Centroid(ST_Collect(geom))) AS lat
            FROM accidents
            WHERE EXTRACT(YEAR FROM datetime) = :year
            GROUP BY province
        """), {"year": year})
        rows = [dict(row._mapping) for row in result]
    return jsonify(rows)

@app.route('/api/cities')
def api_cities():
    year = request.args.get('year')
    province = request.args.get('province')
    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT city, ST_X(ST_Centroid(ST_Collect(geom))) AS lng, ST_Y(ST_Centroid(ST_Collect(geom))) AS lat
            FROM accidents
            WHERE EXTRACT(YEAR FROM datetime) = :year AND province = :province
            GROUP BY city
        """), {"year": year, "province": province})
        rows = [dict(row._mapping) for row in result]
    return jsonify(rows)

@app.route('/api/accidents')
def api_accidents():
    year = request.args.get('year')
    province = request.args.get('province')
    city = request.args.get('city')
    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT ST_Y(geom) AS lat,
                   ST_X(geom) AS lng,
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
