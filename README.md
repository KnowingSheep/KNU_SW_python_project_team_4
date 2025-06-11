
---
### 사용 도구
##### 파이썬 라이브러리
- Flask (웹 서버 구축)
- GeoPandas (위치 데이터 프레임 관리)
- Pandas (CSV 등 데이터프레임 처리)

##### 클라이언트/프론트엔드
- Leaflet.js (지도 및 마커 시각화)
- AJAX (비동기 통신 처리)

##### 데이터베이스
- PostgreSQL + PostGIS (공간 데이터 특화 DB)

##### 외부 API
- 카카오맵 개발자 API (로드뷰 조회 등)
---
### 파이썬 프로그램
##### 데이터 전처리 프로그램
- raw 폴더에 원본 데이터 파일 저장 후 실행 (교통사고 데이터.csv , sig 파일들 등등)
- accident_data_preprocessing.py : 교통사고 데이터 통합
- district_data_preprocessing.py : 시군구 중심 좌표 데이터 생성
-------
