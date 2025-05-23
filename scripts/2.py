import pandas as pd
import folium
from folium import FeatureGroup
from folium.plugins import MarkerCluster

# 사고 데이터 (위도, 경도, 시군구 정보 포함)
accident_df = pd.read_csv("data/통합_한국도로교통공단_사망교통사고_2012-2023.csv").dropna(subset=["위도", "경도", "발생지시군구"])

# 시군구 중심좌표 데이터 (SIG_KOR_NM, 위도, 경도 포함)
center_df = pd.read_csv("data/통합_시군구_중심좌표.csv")
center_df["시군구"] = center_df["SIG_KOR_NM"].str.replace(r"\s", "", regex=True)
accident_df["발생지시군구"] = accident_df["발생지시군구"].str.replace(r"\s", "", regex=True)

# 사고 건수 집계
accident_counts = accident_df.groupby("발생지시군구").size().reset_index(name="사고건수")

# 지도 생성
m = folium.Map(location=[36.5, 127.5], zoom_start=7)

# 시군구별 사고 마커 그룹 저장
layer_dict = {}

for name, group in accident_df.groupby("발생지시군구"):
    fg = FeatureGroup(name=f"{name} 사고 마커", show=False)  # 기본 비활성화
    for _, row in group.iterrows():
        folium.CircleMarker(
            location=[row["위도"], row["경도"]],
            radius=8,
            color="blue",
            fill=True,
            fill_opacity=0.5
        ).add_to(fg)
    fg.add_to(m)
    layer_dict[name] = fg  # 나중에 연결

# 시군구 중심에 사고수 마커 표시
for _, row in accident_counts.iterrows():
    name = row["발생지시군구"]
    cnt = row["사고건수"]

    center = center_df[center_df["시군구"] == name]
    if center.empty:
        continue

    lat = center["위도"].values[0]
    lon = center["경도"].values[0]

    # 팝업에 Layer 이름 안내
    popup = folium.Popup(f"{name} 사고 건수: {cnt}<br>좌측 LayerControl에서 '{name} 사고 마커' 켜기", max_width=300)

    folium.Marker(
        location=[lat, lon],
        popup=popup,
        icon=folium.Icon(color='red', icon='info-sign')
    ).add_to(m)

# LayerControl 추가
folium.LayerControl(collapsed=False).add_to(m)

# 저장
m.save("시군구_사고클러스터_개별연동.html")
