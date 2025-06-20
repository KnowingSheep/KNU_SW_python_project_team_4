import pandas as pd
from sqlalchemy import create_engine
from geoalchemy2 import Geometry
from shapely.geometry import Point
from datetime import datetime
import geopandas as gpd

DB_URL = "postgresql+psycopg2://postgres:1356@localhost:5432/team4db"

# CSV 파일 경로
csv_path = "./data/통합_한국도로교통공단_사망교통사고_2012-2023.csv"

# 1. CSV 로드
df = pd.read_csv(csv_path, encoding='utf-8')

# 2. 필요한 컬럼만 추출 및 가공
df = df[[
    '발생년', '발생년월일시', '주야', '사망자수', '사상자수', '중상자수',
    '경상자수', '부상신고자수', '발생지시도', '발생지시군구',
    '사고유형_대분류', '사고유형_중분류', '사고유형',
    '가해자법규위반', '도로형태_대분류', '도로형태',
    '가해자_당사자종별', '피해자_당사자종별', '경도', '위도'
]]

# 3. 컬럼명 영어로 변경
df.columns = [
    'dateyear', 'datetime_str', 'daytime', 'deaths', 'injured', 'severe_injuries',
    'mild_injuries', 'report_injuries', 'province', 'city',
    'type_major', 'type_minor', 'type_desc',
    'law_violation', 'road_major', 'road_detail',
    'offender_type', 'victim_type', 'lon', 'lat'
]

# 4. 데이터 타입 가공
df['datetime'] = pd.to_datetime(df['datetime_str'], errors='coerce')
df['day'] = df['daytime'].map(lambda x: True if str(x).strip() == '주간' else False)
df['geom'] = df.apply(lambda row: Point(row['lon'], row['lat']), axis=1)

# 💡 정수형 필드 float → int 변환
int_columns = ['deaths', 'injured', 'severe_injuries', 'mild_injuries', 'report_injuries']
for col in int_columns:
    df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0).astype(int)


# 5. GeoDataFrame으로 변환
gdf = gpd.GeoDataFrame(df, geometry='geom', crs='EPSG:4326')

# 6. 불필요한 컬럼 제거
gdf = gdf.drop(columns=['datetime_str', 'daytime', 'lon', 'lat'])

# 7. DB에 저장
engine = create_engine(DB_URL)

gdf.to_postgis(
    name='accidents',
    con=engine,
    if_exists='append',  # 또는 'replace'
    index=False
)
