from flask import Flask, abort, render_template, jsonify, request
from sqlalchemy import create_engine, text
from datetime import datetime

app = Flask(__name__)

DB_URL = "postgresql+psycopg2://postgres:1356@localhost:5432/team4db"
engine = create_engine(DB_URL)

@app.route('/')
def homepage():
    return render_template('index.html')

@app.route('/map')
def map_page():
    return render_template('map.html')

@app.route("/roadview")
def roadview():
    kakao_key = "PUT-API-KEY"  # 카카오 개발자 JavaScript API키 입력
    return render_template("roadview.html", kakao_key=kakao_key)

@app.route('/stats')
def stats_page():
    return render_template('stats.html')

@app.route('/table')
def table_page():
    page         = request.args.get('page', default=1, type=int)
    filter_by    = request.args.get('filter_by', default='', type=str)
    search_value = request.args.get('search_value', default='', type=str)
    per_page     = 50
    offset       = (page - 1) * per_page

    allowed = {
        'dateyear', 'datetime', 'province', 'city',
        'type_major', 'type_minor', 'law_violation'
    }

    base_sql = "FROM accidents"
    params = {}

    if filter_by in allowed and search_value:
        base_sql += f" WHERE {filter_by}::text ILIKE :val"
        params['val'] = f"%{search_value}%"

    select_sql = f"""
        SELECT
            id,
            dateyear,
            to_char(datetime, 'YYYY-MM-DD HH24:MI:SS') AS datetime,
            deaths,
            injured,
            severe_injuries,
            mild_injuries,
            report_injuries,
            province,
            city,
            type_major,
            type_minor,
            type_desc,
            law_violation,
            road_major,
            road_detail,
            offender_type,
            victim_type,
            ST_Y(geom) AS lat,
            ST_X(geom) AS lng
        {base_sql}
        ORDER BY datetime DESC
        LIMIT :limit OFFSET :offset
    """
    params['limit'] = per_page
    params['offset'] = offset

    count_sql = f"SELECT COUNT(*) {base_sql}"

    with engine.connect() as conn:
        result = conn.execute(text(select_sql), params)
        accidents = [dict(r._mapping) for r in result]

        total_count = conn.execute(text(count_sql), params).scalar()
        total_pages = (total_count + per_page - 1) // per_page

    return render_template(
        'table.html',
        accidents=accidents,
        page=page,
        total_pages=total_pages,
        filter_by=filter_by,
        search_value=search_value
    )

@app.route('/api/stats')
def api_stats():
    start = request.args.get("start")
    end = request.args.get("end")

    if not start or not end:
        return jsonify({"error": "start와 end 파라미터가 필요합니다"}), 400

    with engine.connect() as conn:
        # 1. 요약 통계
        summary_query = text("""
            SELECT
                COUNT(*) AS total,
                SUM(deaths) AS fatal,
                ROUND(AVG(deaths), 2) AS avg_severity
            FROM accidents
            WHERE datetime BETWEEN :start AND :end
        """)
        summary = conn.execute(summary_query, {"start": start, "end": end}).mappings().first()

        # 2. 시간대별 사고
        hour_query = text("""
            SELECT EXTRACT(HOUR FROM datetime) AS hour, COUNT(*) AS count
            FROM accidents
            WHERE datetime BETWEEN :start AND :end
            GROUP BY hour ORDER BY hour
        """)
        hour_data = conn.execute(hour_query, {"start": start, "end": end}).mappings().all()
        hour_dict = {int(row["hour"]): row["count"] for row in hour_data}
        hour_result = {
            "labels": [f"{h}시" for h in range(24)],
            "values": [hour_dict.get(h, 0) for h in range(24)]
        }

        # 3. 요일별 사고
        week_query = text("""
            SELECT EXTRACT(DOW FROM datetime) AS dow, COUNT(*) AS count
            FROM accidents
            WHERE datetime BETWEEN :start AND :end
            GROUP BY dow ORDER BY dow
        """)
        week_data = conn.execute(week_query, {"start": start, "end": end}).mappings().all()
        weekday_map = ["일", "월", "화", "수", "목", "금", "토"]
        week_dict = {int(row["dow"]): row["count"] for row in week_data}
        week_result = {
            "labels": weekday_map,
            "values": [week_dict.get(i, 0) for i in range(7)]
        }

        # 4. 지역별 사고 (상위 10개 province)
        region_query = text("""
            SELECT province, COUNT(*) AS count
            FROM accidents
            WHERE datetime BETWEEN :start AND :end
            GROUP BY province
            ORDER BY count DESC
            LIMIT 10
        """)
        region_data = conn.execute(region_query, {"start": start, "end": end}).mappings().all()
        region_result = {
            "labels": [row["province"] for row in region_data],
            "values": [row["count"] for row in region_data]
        }

        # 5. 월별 사고 추이
        month_query = text("""
            SELECT EXTRACT(MONTH FROM datetime) AS month, COUNT(*) AS count
            FROM accidents
            WHERE datetime BETWEEN :start AND :end
            GROUP BY month ORDER BY month
        """)
        month_data = conn.execute(month_query, {"start": start, "end": end}).mappings().all()
        month_dict = {int(row["month"]): row["count"] for row in month_data}
        trend_result = {
            "labels": [f"{m}월" for m in range(1, 13)],
            "values": [month_dict.get(m, 0) for m in range(1, 13)]
        }

    return jsonify({
        "total": summary["total"],
        "fatal": int(summary["fatal"]) if summary["fatal"] is not None else 0,
        "avg_severity": float(summary["avg_severity"]) if summary["avg_severity"] is not None else 0.0,
        "hour": hour_result,
        "week": week_result,
        "region": region_result,
        "trend": trend_result
    })

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

        # 시도
        result = conn.execute(text("SELECT DISTINCT province FROM provinces ORDER BY province"))
        filters["provinces"] = [row[0] for row in result]

        # 시군구를 시도별로 그룹핑
        result = conn.execute(text("SELECT province, city FROM districts ORDER BY province, city"))
        districts = {}
        for row in result:
            prov = row.province
            city = row.city
            districts.setdefault(prov, []).append(city)
        filters["districts_by_province"] = districts

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
    province = request.args.get("province")
    city = request.args.get("city")

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
        query += f" AND EXTRACT(DOW FROM datetime) IN ({placeholders})"
        for i, day in enumerate(days):
            params[f"dow{i}"] = int(day)

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

    #시/도
    if province:
        query += " AND province = :province"
        params["province"] = province

    #시/군/구
    if city:
        query += " AND city = :city"
        params["city"] = city

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

@app.route('/api/accident/<int:accident_id>')
def get_accident_detail(accident_id):
    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT 
                id,
                lat,
                lng,
                to_char(datetime, 'YYYY-MM-DD') AS date,
                province,
                city,
                type_major,
                type_minor,
                type_desc,
                law_violation,
                road_major,
                offender_type,
                victim_type
            FROM accidents
            WHERE id = :id
        """), {"id": accident_id})

        row = result.fetchone()
        if not row:
            return jsonify({"error": "not found"}), 404
        
        return jsonify(dict(row._mapping))


@app.route('/api/stats/summary')
def api_stats_summary():
    with engine.connect() as conn:
        # 1. 사고 최다 발생 연도
        year_res = conn.execute(text("""
            SELECT EXTRACT(YEAR FROM datetime) AS year, COUNT(*) AS cnt
            FROM accidents
            GROUP BY year
            ORDER BY cnt DESC
            LIMIT 1
        """)).fetchone()
        top_year = int(year_res.year)

        # 2. 해당 연도의 최다 요일
        weekday_res = conn.execute(text("""
            SELECT to_char(datetime, 'Day') AS weekday, COUNT(*) AS cnt
            FROM accidents
            WHERE EXTRACT(YEAR FROM datetime) = :year
            GROUP BY weekday
            ORDER BY cnt DESC
            LIMIT 1
        """), {"year": top_year}).fetchone()
        top_weekday = weekday_res.weekday.strip() if weekday_res else "정보 없음"

        # 3. 해당 연도의 최다 시도
        province_res = conn.execute(text("""
            SELECT province, COUNT(*) AS cnt
            FROM accidents
            WHERE EXTRACT(YEAR FROM datetime) = :year
            GROUP BY province
            ORDER BY cnt DESC
            LIMIT 1
        """), {"year": top_year}).fetchone()
        top_province = province_res.province if province_res else "정보 없음"

    return jsonify({
        "year": top_year,
        "top_weekday": top_weekday,
        "top_province": top_province
    })




if __name__ == '__main__':
    app.run(debug=True)
