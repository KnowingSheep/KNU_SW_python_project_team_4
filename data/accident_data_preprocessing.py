import pandas as pd
import folium
import glob
import os

#발생년월일시 통일
def extract_datetime(row):
    try:
        base_time = pd.to_datetime(str(row['발생년월일시']), errors='coerce')
        if pd.notna(base_time) and pd.notna(row['발생분']):
            return base_time + pd.to_timedelta(int(row['발생분']), unit='m')
        return base_time
    except:
        return pd.NaT

#사상자수 계산
def calc_casualties(row):
    if pd.notna(row.get('사상자수')):
        return row['사상자수']
    else:
        return sum([
            row.get('사망자수', 0) or 0,
            row.get('중상자수', 0) or 0,
            row.get('경상자수', 0) or 0
        ])

# CSV 파일들이 있는 폴더 경로
folder_path = 'raw/'

# 해당 폴더 내 모든 CSV 파일 경로 가져오기
all_files = glob.glob(os.path.join(folder_path, "*.csv"))

# 파일들을 모두 읽어서 리스트로 저장
df_list = []

for file in all_files:
    df = pd.read_csv(file, encoding='cp949')  # or 'utf-8' depending on your file
    df_list.append(df)

# 하나로 합치기
merged_df = pd.concat(df_list, ignore_index=True)
merged_df['발생년월일시'] = merged_df.apply(extract_datetime, axis=1)
merged_df.drop('발생분', axis=1, inplace=True)
merged_df['사상자수'] = merged_df.apply(calc_casualties, axis=1)
merged_df.drop('부상자수', axis=1, inplace=True)
merged_df['발생지시군구'] = merged_df['발생지시군구'].str.replace('(통합)', '', regex=False).str.strip()

# 결과 저장
merged_df.to_csv("통합_한국도로교통공단_사망교통사고_2012-2023.csv", index=False, encoding='utf-8-sig')

print('통합_한국도로교통공단_사망교통사고_2012-2023.csv 파일 저장 완료')
