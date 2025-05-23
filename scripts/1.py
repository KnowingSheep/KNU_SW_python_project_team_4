import pandas as pd
import folium
import json
from folium.plugins import MarkerCluster

df = pd.read_csv('통합_사고데이터.csv', encoding='utf-8-sig', low_memory=False)

df = df[['위도', '경도', '사고유형_대분류', '발생년월일시']].dropna()
df['발생년월일일시'] = pd.to_datetime(df['발생년월일시'])

location_counts = df.groupby(['위도', '경도']).size().reset_index(name='사고건수')

top_locations = location_counts.sort_values(by='사고건수', ascending=False)

# 지도 초기 위치 설정 (예: 서울 중심)
m = folium.Map(location=[37.5665, 126.9780], zoom_start=11)

marker_cluster = MarkerCluster().add_to(m)

# 사고 위치 마커 표시
for _, row in top_locations.iterrows():
    folium.CircleMarker(
        location=[row['위도'], row['경도']],
        radius=10,  # 사고건수에 따라 크기 조절
        color='red',
        fill=True,
        fill_opacity=0.6,
        popup=f"사고건수: {row['사고건수']}"
    ).add_to(marker_cluster)

# 지도 저장
m.save('교통사고_위험지도.html')
