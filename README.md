#사용 라이브러리\r
파이썬 라이브러리
Flask(웹 서버 구축)
geopandas(위치 데이터 프레임 관리)
pandas(csv 등의 데이터 프레임 관리)
-----
외부 라이브러리
leaflet.js(지도 및 마커 표시)
AJAX(비동기 데이터 전송)
PostgreSQL+PostGIS(위치 데이터 쿼리 성능 특화 DB)
카카오맵 개발자 API(개별 사건 데이터 로드뷰)
----------------------------------
#통합 데이터 csv 파일 생성
-------
raw 폴더에 원본 데이터 파일 저장 (교통사고 데이터.csv , sig 파일들 등등)
accident_data_preprocessing.py : 교통사고 데이터 통합
district_data_preprocessing.py : 시군구 중심 좌표 데이터 생성
-------
