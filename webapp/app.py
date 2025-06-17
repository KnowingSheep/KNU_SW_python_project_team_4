from flask import Flask, abort, render_template, jsonify, request
from sqlalchemy import create_engine, text
from datetime import datetime

app = Flask(__name__)

DB_URL = "postgresql+psycopg2://postgres:1356@localhost:5432/team4db"
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
    year = request.args.get('year', type=int)
    province = request.args.get('province')
    city = request.args.get('city')

    if not (year and province and city):
        abort(400, description="'year', 'province', and 'city' parameters are required")

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

@app.route("/api/filters")
def api_filters():
    with engine.connect() as conn:
        filters = {}

        for col, key in [
            ("type_major", "types_major"),
            ("type_minor", "types_minor"),
            ("law_violation", "violations"),
            ("road_major", "roads"),
            ("offender_type", "offenders"),
            ("victim_type", "victims")
        ]:
            result = conn.execute(text(f"""
                SELECT DISTINCT {col}
                FROM accidents
                WHERE {col} IS NOT NULL AND TRIM({col}) != ''
                ORDER BY {col}
            """))
            filters[key] = [row[0] for row in result]

    return jsonify(filters)

@app.route('/api/filtered_accidents')
def api_filtered_accidents():
    start_raw = request.args.get('start')
    end_raw = request.args.get('end')
    timeofday = request.args.get('timeofday')
    days_raw = request.args.get('dayofweek')
    types = request.args.get('types', '').split(',')
    type_minors = request.args.get('type_minor', '').split(',')
    roads = request.args.get('road', '').split(',')
    offenders = request.args.get('offender', '').split(',')
    victims = request.args.get('victim', '').split(',')
    violations = request.args.get('violation', '').split(',')

    query = """
        SELECT id, lat, lng,
               to_char(datetime, 'YYYY-MM-DD') AS date,
               CONCAT(type_desc, ' - ', law_violation) AS desc,
               type_major
        FROM accidents
        WHERE 1=1
    """
    params = {}

    # 날짜 조건
    if start_raw:
        try:
            start = datetime.strptime(start_raw, "%Y-%m-%d")
            query += " AND datetime >= :start"
            params["start"] = start
        except ValueError:
            abort(400, "'start' 형식 오류")
    if end_raw:
        try:
            end = datetime.strptime(end_raw, "%Y-%m-%d")
            query += " AND datetime <= :end"
            params["end"] = end
        except ValueError:
            abort(400, "'end' 형식 오류")

    # 주야 조건
    if timeofday == 'day':
        query += " AND EXTRACT(HOUR FROM datetime) BETWEEN 6 AND 17"
    elif timeofday == 'night':
        query += " AND (EXTRACT(HOUR FROM datetime) < 6 OR EXTRACT(HOUR FROM datetime) > 17)"

    # 요일 다중
    if days_raw:
        days = days_raw.split(',')
        placeholders = ','.join([f":dow{i}" for i in range(len(days))])
        query += f" AND TO_CHAR(datetime, 'DY', 'NLS_DATE_LANGUAGE=KOREAN') IN ({placeholders})"
        for i, day in enumerate(days):
            params[f"dow{i}"] = day

    # 사고 대분류
    if types and types[0]:
        placeholders = ','.join([f":type_{i}" for i in range(len(types))])
        query += f" AND type_major IN ({placeholders})"
        for i, val in enumerate(types):
            params[f"type_{i}"] = val

    # 사고 소분류
    if type_minors and type_minors[0]:
        placeholders = ','.join([f":minor_{i}" for i in range(len(type_minors))])
        query += f" AND type_minor IN ({placeholders})"
        for i, val in enumerate(type_minors):
            params[f"minor_{i}"] = val

    # 기타 조건
    def add_list_filter(param_list, field, prefix):
        if param_list and param_list[0]:
            placeholders = ','.join([f":{prefix}_{i}" for i in range(len(param_list))])
            nonlocal query
            query += f" AND {field} IN ({placeholders})"
            for i, val in enumerate(param_list):
                params[f"{prefix}_{i}"] = val

    add_list_filter(roads, "road_major", "road")
    add_list_filter(offenders, "offender_type", "off")
    add_list_filter(victims, "victim_type", "vic")
    add_list_filter(violations, "law_violation", "viol")

    with engine.connect() as conn:
        result = conn.execute(text(query), params)
        rows = [dict(row._mapping) for row in result]

    return jsonify(rows)


@app.route('/test')
def test():
    return render_template('roadView.html')

if __name__ == '__main__':
    app.run(debug=True)
