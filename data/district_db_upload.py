import pandas as pd
import geopandas as gpd
from shapely.geometry import Point
from sqlalchemy import create_engine

# DB 접속 정보
DB_URL = "postgresql+psycopg2://postgres:1356@localhost:5432/team4db"
engine = create_engine(DB_URL)

# ===== 시도 테이블 업로드 =====
def upload_sido():
    df = pd.read_csv("./data/통합_시도_중심좌표.csv", encoding="utf-8")
    df["geometry"] = df.apply(lambda row: Point(row["경도"], row["위도"]), axis=1)
    gdf = gpd.GeoDataFrame(df, geometry="geometry", crs="EPSG:4326")

    gdf = gdf.rename(columns={"SIG_CD": "sig_cd", "시도": "province", "위도": "lat", "경도": "lng"})
    gdf = gdf[["sig_cd", "province", "lat", "lng", "geometry"]]

    gdf.to_postgis("provinces", con=engine, if_exists="replace", index=False)

# ===== 시군구 테이블 업로드 =====
def upload_sigungu():
    df = pd.read_csv("./data/통합_시군구_중심좌표.csv", encoding="utf-8")
    df["geometry"] = df.apply(lambda row: Point(row["경도"], row["위도"]), axis=1)
    gdf = gpd.GeoDataFrame(df, geometry="geometry", crs="EPSG:4326")

    gdf = gdf.rename(columns={"SIG_CD": "sig_cd", "시도": "province", "시군구": "city", "위도": "lat", "경도": "lng"})
    gdf = gdf[["sig_cd", "province", "city", "lat", "lng", "geometry"]]

    gdf.to_postgis("districts", con=engine, if_exists="replace", index=False)

# 실행
upload_sido()
upload_sigungu()
