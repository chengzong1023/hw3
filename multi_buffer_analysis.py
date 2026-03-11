import geopandas as gpd
import pandas as pd
import os
from dotenv import load_dotenv

# 載入環境變數
load_dotenv()

print("=== 多級緩衝區分析 (Multi-Buffer Risk Zoning) ===")
print()

# 讀取緩衝區參數
BUFFER_HIGH = int(os.getenv('BUFFER_HIGH', 500))
BUFFER_MED = int(os.getenv('BUFFER_MED', 1000))
BUFFER_LOW = int(os.getenv('BUFFER_LOW', 2000))

print(f"緩衝區參數：")
print(f"  高風險緩衝區：{BUFFER_HIGH} 公尺")
print(f"  中風險緩衝區：{BUFFER_MED} 公尺")
print(f"  低風險緩衝區：{BUFFER_LOW} 公尺")
print()

# 載入已準備好的資料
print("載入分析資料...")

# 載入河川資料
rivers = gpd.read_file('river_data/riverpoly/riverpoly.shp')
if rivers.crs != 'EPSG:3826':
    rivers = rivers.to_crs('EPSG:3826')
print(f"河川資料：{len(rivers)} 個河川面 (CRS: {rivers.crs})")

# 載入避難所資料
shelters = gpd.read_file('shelters_cleaned_3826.geojson')
print(f"避難所資料：{len(shelters)} 個避難所 (CRS: {shelters.crs})")

# 載入鄉鎮區資料
townships = gpd.read_file('townships_3826.geojson')
print(f"鄉鎮區資料：{len(townships)} 個鄉鎮區 (CRS: {townships.crs})")

print()

# 1. 建立三級河川警戒緩衝區
print("1. 建立三級河川警戒緩衝區")

# 建立緩衝區（必須在 EPSG:3826 下進行）
print("建立河川緩衝區...")
river_buffers_high = rivers.buffer(BUFFER_HIGH)
river_buffers_med = rivers.buffer(BUFFER_MED)
river_buffers_low = rivers.buffer(BUFFER_LOW)

print(f"高風險緩衝區 ({BUFFER_HIGH}m)：{len(river_buffers_high)} 個多邊形")
print(f"中風險緩衝區 ({BUFFER_MED}m)：{len(river_buffers_med)} 個多邊形")
print(f"低風險緩衝區 ({BUFFER_LOW}m)：{len(river_buffers_low)} 個多邊形")

# 轉換為 GeoDataFrame
buffer_high_gdf = gpd.GeoDataFrame(geometry=river_buffers_high, crs='EPSG:3826')
buffer_med_gdf = gpd.GeoDataFrame(geometry=river_buffers_med, crs='EPSG:3826')
buffer_low_gdf = gpd.GeoDataFrame(geometry=river_buffers_low, crs='EPSG:3826')

# 溶解（dissolve）建立統一緩衝區
print("溶解緩衝區建立統一風險區...")
buffer_high_unified = buffer_high_gdf.dissolve()
buffer_med_unified = buffer_med_gdf.dissolve()
buffer_low_unified = buffer_low_gdf.dissolve()

print(f"統一高風險區：{len(buffer_high_unified)} 個區域")
print(f"統一中風險區：{len(buffer_med_unified)} 個區域")
print(f"統一低風險區：{len(buffer_low_unified)} 個區域")

# 儲存緩衝區
buffer_high_unified.to_file('buffer_high_risk.geojson', driver='GeoJSON')
buffer_med_unified.to_file('buffer_med_risk.geojson', driver='GeoJSON')
buffer_low_unified.to_file('buffer_low_risk.geojson', driver='GeoJSON')

print("緩衝區已儲存為 GeoJSON 檔案")
print()

# 2. 空間連接 (Spatial Join)
print("2. 空間連接找出各級緩衝區內的避難所")

# 初始化避難所風險等級為 'safe'
shelters['risk_level'] = 'safe'
shelters['risk_distance'] = None

# 使用空間連接找出各級緩衝區內的避難所
print("執行空間連接...")

# 高風險區
shelters_in_high = gpd.sjoin(shelters, buffer_high_unified, how='inner', predicate='intersects')
print(f"高風險區內避難所：{len(shelters_in_high)} 個")

# 中風險區
shelters_in_med = gpd.sjoin(shelters, buffer_med_unified, how='inner', predicate='intersects')
print(f"中風險區內避難所：{len(shelters_in_med)} 個")

# 低風險區
shelters_in_low = gpd.sjoin(shelters, buffer_low_unified, how='inner', predicate='intersects')
print(f"低風險區內避難所：{len(shelters_in_low)} 個")

# 處理一對多問題：取最高風險等級
print("\n處理風險等級標記（優先順序：高 > 中 > 低 > 安全）...")

# 高風險優先
shelters.loc[shelters.index.isin(shelters_in_high.index), 'risk_level'] = 'high'
shelters.loc[shelters.index.isin(shelters_in_high.index), 'risk_distance'] = BUFFER_HIGH

# 中風險（未被標記為高風險的）
med_indices = shelters_in_med.index.difference(shelters_in_high.index)
shelters.loc[med_indices, 'risk_level'] = 'medium'
shelters.loc[med_indices, 'risk_distance'] = BUFFER_MED

# 低風險（未被標記為高、中風險的）
low_indices = shelters_in_low.index.difference(shelters_in_high.index).difference(shelters_in_med.index)
shelters.loc[low_indices, 'risk_level'] = 'low'
shelters.loc[low_indices, 'risk_distance'] = BUFFER_LOW

# 統計各風險等級的避難所數量
risk_counts = shelters['risk_level'].value_counts()
print(f"\n風險等級統計：")
for level, count in risk_counts.items():
    percentage = count / len(shelters) * 100
    print(f"  {level}：{count} 個 ({percentage:.1f}%)")

print()

# 3. 風險等級詳細分析
print("3. 風險等級詳細分析")

# 按縣市統計風險分布
if 'COUNTYNAME' in townships.columns:
    # 將避難所與鄉鎮區進行空間連接
    shelters_with_township = gpd.sjoin(shelters, townships, how='inner', predicate='within')
    
    print("各縣市風險避難所分布：")
    county_risk_stats = shelters_with_township.groupby(['COUNTYNAME', 'risk_level']).size().unstack(fill_value=0)
    
    for county in county_risk_stats.index:
        high = county_risk_stats.loc[county, 'high'] if 'high' in county_risk_stats.columns else 0
        med = county_risk_stats.loc[county, 'medium'] if 'medium' in county_risk_stats.columns else 0
        low = county_risk_stats.loc[county, 'low'] if 'low' in county_risk_stats.columns else 0
        safe = county_risk_stats.loc[county, 'safe'] if 'safe' in county_risk_stats.columns else 0
        total = high + med + low + safe
        
        if high > 0:  # 只顯示有高風險避難所的縣市
            print(f"  {county}：高{high} 中{med} 低{low} 安全{safe} (總計{total})")

print()

# 4. 儲存結果
print("4. 儲存分析結果")

# 儲存帶有風險等級的避難所資料
shelters.to_file('shelters_with_risk_level.geojson', driver='GeoJSON')
print("已儲存 shelters_with_risk_level.geojson")

# 建立風險審計報告
risk_audit = shelters[['risk_level', 'risk_distance']].copy()
risk_audit['shelter_id'] = shelters.index

# 添加其他重要欄位
if '避難所名稱' in shelters.columns:
    risk_audit['shelter_name'] = shelters['避難所名稱']
if '避難所地址' in shelters.columns:
    risk_audit['address'] = shelters['避難所地址']
if '可容納人數' in shelters.columns:
    risk_audit['capacity'] = shelters['可容納人數']

# 儲存為 JSON
risk_audit.to_json('shelter_risk_audit.json', orient='records', indent=2, force_ascii=False)
print("已儲存 shelter_risk_audit.json")

print()

# 5. 總結報告
print("=== 多級緩衝區分析完成 ===")
print(f"總避難所數量：{len(shelters)}")
print(f"高風險避難所：{risk_counts.get('high', 0)} 個 ({risk_counts.get('high', 0)/len(shelters)*100:.1f}%)")
print(f"中風險避難所：{risk_counts.get('medium', 0)} 個 ({risk_counts.get('medium', 0)/len(shelters)*100:.1f}%)")
print(f"低風險避難所：{risk_counts.get('low', 0)} 個 ({risk_counts.get('low', 0)/len(shelters)*100:.1f}%)")
print(f"安全避難所：{risk_counts.get('safe', 0)} 個 ({risk_counts.get('safe', 0)/len(shelters)*100:.1f}%)")

print("\n輸出檔案：")
print("- buffer_high_risk.geojson (高風險緩衝區)")
print("- buffer_med_risk.geojson (中風險緩衝區)")
print("- buffer_low_risk.geojson (低風險緩衝區)")
print("- shelters_with_risk_level.geojson (避難所風險等級)")
print("- shelter_risk_audit.json (風險審計報告)")

print("\n準備進行收容量缺口分析...")
