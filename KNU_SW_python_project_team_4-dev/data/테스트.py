import pandas as pd
import folium
import os
from folium.plugins import MarkerCluster

csv_path = r'C:\Users\dlwns\Desktop\새 폴더\통합_한국도로교통공단_사망교통사고_2012-2023.csv'
if not os.path.isfile(csv_path):
    raise FileNotFoundError(f"CSV 파일을 찾을 수 없습니다: {csv_path}")

df = pd.read_csv(csv_path)
df = df.dropna(subset=['위도', '경도'])

threshold = df['사망자수'].quantile(0.8)
df_top20 = df[df['사망자수'] >= threshold]

max_markers = 500
if len(df_top20) > max_markers:
    df_plot = df_top20.sample(n=max_markers, random_state=42)
else:
    df_plot = df_top20

center_lat = df_plot['위도'].mean()
center_lon = df_plot['경도'].mean()

m = folium.Map(location=[center_lat, center_lon], zoom_start=7)

cluster = MarkerCluster().add_to(m)

for _, row in df_plot.iterrows():
    folium.Marker(
        location=[row['위도'], row['경도']],
        popup=(f"발생일시: {row.get('발생년월일시','')}\n"
               f"사망자수: {row.get('사망자수','')}"),
        icon=folium.Icon(color='red', icon='info-sign')
    ).add_to(cluster)

output_path = 'fatal_accidents_sampled.html'
m.save(output_path)
print(f"자동 샘플링 후 지도 파일이 '{output_path}'에 저장되었습니다 (총 {len(df_plot)}개 마커).")
