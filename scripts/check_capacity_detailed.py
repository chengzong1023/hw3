import pandas as pd
import geopandas as gpd

print('檢查收容人數欄位的實際內容...')
print()

# 載入原始資料
df = pd.read_csv('data/避難所clean.csv', encoding='utf-8')

# 檢查可容納人數欄位
if '可容納人數' in df.columns:
    print('可容納人數欄位分析：')
    print(f'  總記錄數：{len(df)}')
    print(f'  非空值數量：{df["可容納人數"].notna().sum()}')
    print(f'  空值數量：{df["可容納人數"].isna().sum()}')
    print(f'  數值範圍：{df["可容納人數"].min()} ~ {df["可容納人數"].max()}')
    print(f'  平均值：{df["可容納人數"].mean():.1f}')
    print(f'  前10個值：{df["可容納人數"].dropna().head(10).tolist()}')
else:
    print('未找到可容納人數欄位')

# 檢查其他可能的收容欄位
print('\n其他可能的收容欄位：')
for col in df.columns:
    if '容' in col or 'capacity' in col.lower():
        print(f'  {col}')
        if col in df.columns:
            non_null_count = df[col].notna().sum()
            print(f'    非空值：{non_null_count}/{len(df)}')

# 檢查 GeoJSON 檔案中的收容欄位
print('\n檢查 GeoJSON 檔案...')
gdf = gpd.read_file('shelters_clean_with_risk.geojson')
print(f'GeoJSON 欄位：{list(gdf.columns)}')

# 檢查 GeoJSON 中的收容欄位
geo_capacity_cols = []
for col in gdf.columns:
    if '容納' in col or 'capacity' in col.lower():
        geo_capacity_cols.append(col)
        print(f'GeoJSON 找到收容欄位：{col}')

# 檢查模擬收容人數欄位
if '模擬收容人數' in gdf.columns:
    print('\n模擬收容人數欄位分析：')
    print(f'  總記錄數：{len(gdf)}')
    print(f'  非空值數量：{gdf["模擬收容人數"].notna().sum()}')
    print(f'  數值範圍：{gdf["模擬收容人數"].min()} ~ {gdf["模擬收容人數"].max()}')
    print(f'  平均值：{gdf["模擬收容人數"].mean():.1f}')
else:
    print('\n未找到模擬收容人數欄位')

# 比較原始資料和 GeoJSON
print('\n資料對比：')
print(f'原始 CSV 記錄數：{len(df)}')
print(f'GeoJSON 記錄數：{len(gdf)}')

if '可容納人數' in df.columns and '模擬收容人數' in gdf.columns:
    original_capacity = df['可容納人數'].notna().sum()
    simulated_capacity = gdf['模擬收容人數'].sum()
    print(f'原始收容人數總和：{original_capacity}')
    print(f'模擬收容人數總和：{simulated_capacity}')
    print(f'差異：{abs(original_capacity - simulated_capacity)}')
