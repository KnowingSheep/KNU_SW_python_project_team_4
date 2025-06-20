# 🚧 교통사고 분석 시스템

> **데이터 기반의 시각화와 분석으로 교통사고를 예방하고 더 안전한 도로 환경을 만듭니다.**  
> 파이썬 기반 빅데이터 분석 기초 - 기말 프로젝트 (4조)

---

## 📌 프로젝트 개요

본 프로젝트는 2012년부터 2023년까지의 교통사고 데이터를 기반으로 다양한 조건에 따라 사고를 분석하고 시각화하는 시스템입니다.  
지도 기반 사고 위치 시각화, 대시보드를 통한 통계 분석, 표 기반 데이터 조회 기능을 제공합니다.

---

## 🗂️ 주요 기능

| 메뉴 | 설명 |
|------|------|
| 🗺️ 사고 지도 분석 | Leaflet 기반으로 필터링된 사고 데이터를 지도 위에 시각화하고, 로드뷰로 위치 확인 가능 |
| 📊 통계 대시보드 | 연도별, 시간대별, 지역별, 요일별 사고 통계를 인터랙티브 차트로 분석 |
| 📄 데이터 조회 | 사고 데이터를 표 형태로 열람하고, 필터링 및 페이징 기능 제공 |

---

## 🖥️ 실행 방법

### 1. 의존성 설치
```bash
pip install -r requirements.txt
```

### 2. Flask 서버 실행
```bash
python app.py
```

### 3. 웹 접속
```text
http://localhost:5000
```

---

## 📁 프로젝트 구조

```
.
├── data/
│   ├── raw/
│   │   └── put-data-here.txt
│   ├── accident_data_preprocessing.py
│   ├── accidents_db_upload.py
│   ├── district_data_preprocessing.py
│   └── district_db_upload.py
├── static/
│   ├── css/
│   │   ├── index.css
│   │   ├── map.css
│   │   ├── stats.css
│   │   └── table.css
│   ├── js/
│   │   ├── map.js
│   │   └── stats.js
│   └── svg/
│       ├── cs.svg
│       ├── cvc.svg
│       └── cvm.svg
├── templates/
│   ├── index.html
│   ├── map.html
│   ├── roadview.html
│   ├── stats.html
│   └── table.html
├── app.py
├── README.md
└── requirements.txt
```

---

## 👥 팀 소개

- 팀명: 4조
- 팀원:
  - 2021110634 손인수
  - 2021115155 양지원
  - 2021115832 이준서

---

## 📌 향후 개선 방향

- 사고 예측 AI 모델 연동
- 모바일 대응 UI 개선
- 사고 위험 지역 표시

---

## 🛠️ 사용 도구

### 🐍 파이썬 라이브러리
- **Flask**: 웹 서버 및 API 처리
- **pandas**: 교통사고 CSV 데이터 처리
- **geopandas**: 공간 데이터프레임 처리 (행정구역 등)
- **shapely**: 좌표 기반 geometry 생성
- **SQLAlchemy**: PostgreSQL 연결 및 ORM 처리
- **geoalchemy2**: 공간 데이터(geometry)를 DB에 업로드할 때 사용

### 🌐 클라이언트/프론트엔드
- **Leaflet.js**: 지도 및 마커 시각화
- **Fetch API**: 비동기 통신 데이터 처리

### 🗄️ 데이터베이스
- **PostgreSQL + PostGIS**: 공간 데이터 특화 DB

### 🌏 외부 API
- **카카오맵 Javascript API**: 로드뷰 조회 (일 300,000건 호출 무료 제공)

---

## 🐍 파이썬 프로그램

### 데이터 전처리 및 업로드 프로그램
- `raw/` 폴더에 원본 데이터 파일(csv, sig 등) 저장 후 실행
- `accident_data_preprocessing.py`: 교통사고 데이터 통합
- `district_data_preprocessing.py`: 시군구 중심 좌표 데이터 생성
- `accidents_db_upload.py`: `accidents` 테이블로 DB 업로드
- `district_db_upload.py`: `province`, `districts` 테이블로 DB 업로드

---

## 🗃️ 데이터베이스 구조 (PostgreSQL + PostGIS)

### accidents (사고 데이터 테이블)
| 필드명 | 타입 | 설명 |
|--------|------|------|
| id               | integer                       | 사고 ID (PK)             |
| dateyear         | integer                       | 사고 발생 연도           |
| datetime         | timestamp without time zone   | 사고 발생 일시           |
| day              | boolean                       | 주간(True)/야간(False)  |
| deaths           | integer                       | 사망자 수                |
| injured          | integer                       | 부상자 수 (총합)         |
| severe_injuries  | integer                       | 중상자 수                |
| mild_injuries    | integer                       | 경상자 수                |
| report_injuries  | integer                       | 신고만 된 부상자 수      |
| province         | text                          | 시/도                    |
| city             | text                          | 시/군/구                 |
| type_major       | text                          | 사고 대분류              |
| type_minor       | text                          | 사고 소분류              |
| type_desc        | text                          | 사고 상세 설명           |
| law_violation    | text                          | 법규 위반 항목           |
| road_major       | text                          | 도로 종류 (대분류)       |
| road_detail      | text                          | 도로 상세조건            |
| offender_type    | text                          | 가해 차량 유형           |
| victim_type      | text                          | 피해 차량 유형           |
| geom             | geometry (PostGIS)            | 사고 위치 좌표           |
| lat              | double precision              | 위도 (시각화용)          |
| lng              | double precision              | 경도 (시각화용)          |

### provinces (시도 중심좌표)
| 필드명   | 타입              | 설명           |
|----------|-------------------|----------------|
| sig_cd   | character varying | 시도 코드      |
| province | text              | 시도명         |
| lat      | double precision  | 중심 위도      |
| lng      | double precision  | 중심 경도      |
| geometry | geometry          | 경계 폴리곤    |

### districts (시군구 중심좌표)
| 필드명   | 타입              | 설명                 |
|----------|-------------------|----------------------|
| sig_cd   | character varying | 시군구 코드          |
| province | text              | 소속 시도명          |
| city     | text              | 시군구명             |
| lat      | double precision  | 중심 위도            |
| lng      | double precision  | 중심 경도            |
| geometry | geometry          | 행정구역 경계 폴리곤 |

---

## 데이터 출처

### 📊 교통사고 데이터

- **출처:** 한국도로교통공단 (https://www.koroad.or.kr/)
- **기간:** 2012년 ~ 2023년
- **형식:** CSV (UTF-8 인코딩)

### 📍 교통사고 SVG 마커

| 사고 유형 | 아이콘 설명 | 출처 |
|-----------|-------------|------|
| 차대사람 | 🚶‍♂️ 차량-보행자 사고 | [svgrepo.com/car-run-over-man](https://www.svgrepo.com/svg/123641/car-run-over-man) |
| 차대차   | 🚗 차량 간 충돌        | [svgrepo.com/car-crash](https://www.svgrepo.com/svg/117734/car-crash) |
| 차량단독 | 🛞 단독 사고 (전복 등) | [svgrepo.com/car-breakdown](https://www.svgrepo.com/svg/141394/car-breakdown) |