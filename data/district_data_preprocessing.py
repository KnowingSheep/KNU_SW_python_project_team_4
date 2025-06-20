import geopandas as gpd
import pandas as pd

#행정구역 코드 앞부분 맵 (도 구분용)
sido_code_map = {
    '11': '서울',
    '26': '부산',
    '27': '대구',
    '28': '인천',
    '29': '광주',
    '30': '대전',
    '31': '울산',
    '36': '세종',
    '41': '경기',
    '51': '강원',
    '43': '충북',
    '44': '충남',
    '45': '전북',
    '46': '전남',
    '47': '경북',
    '48': '경남',
    '50': '제주'
}


# 출력 제한 해제: 모든 열 보기
pd.set_option('display.max_rows', None)
# Shapefile 불러오기 (같은 폴더에 .shx, .dbf 등도 함께 있어야 함)
gdf = gpd.read_file('raw/sig.shp', encoding='cp949')

gdf.set_crs(epsg=5179, inplace=True)

# 컬럼명(데이터 구조) 확인
print("📌 컬럼 목록:")
print(gdf.columns)

# 좌표계 (CRS: Coordinate Reference System) 확인
print("\n📌 좌표계 (CRS):")
print(gdf.crs)

# 데이터 샘플 확인 (앞부분 5개)
print("\n📌 데이터 샘플:")
print(gdf.head())

gdf = gdf.to_crs(epsg=4326)

# 중심점(centroid) 좌표 추가
gdf['위도'] = gdf.geometry.centroid.y
gdf['경도'] = gdf.geometry.centroid.x

#행정구역코드 앞 두자리로 '시도' 구
gdf['시도'] = gdf['SIG_CD'].str[:2].map(sido_code_map)

#데이터 프레임 형식 통
gdf = gdf[['SIG_CD', '시도', 'SIG_KOR_NM', '위도', '경도']]

#추가 파일 합병
adf = pd.read_csv('raw/시군구_중심좌표_추가.csv', encoding='utf-8-sig')
gdf = pd.concat([gdf,adf], ignore_index=True)

gdf.to_csv('통합_시군구_중심좌표.csv', index=False, encoding='utf-8-sig')

print('통합_시군구_중심좌표.csv 파일 저장 완료')
