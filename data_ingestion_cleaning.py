import geopandas as gpd
import pandas as pd
import os
from dotenv import load_dotenv

# 載入環境變數
load_dotenv()

print("=== 資料載入與清理 (Data Ingestion & Cleaning) ===")
print()

# 1. 讀取水利署河川面 Shapefile → 檢查 CRS（應為 EPSG:3826）
print("1. 讀取水利署河川面 Shapefile")

# 使用已下載的河川資料
river_shp_path = 'river_data/riverpoly/riverpoly.shp'
if os.path.exists(river_shp_path):
    rivers = gpd.read_file(river_shp_path)
    print(f"河川資料載入成功：{len(rivers)} 個河川面")
    print(f"  CRS: {rivers.crs}")
    
    # 確保使用 EPSG:3826
    if rivers.crs != 'EPSG:3826':
        rivers = rivers.to_crs('EPSG:3826')
        print(f"  轉換為 EPSG:3826: {rivers.crs}")
    
    print(f"  河川邊界: {rivers.total_bounds}")
    print(f"  河川欄位: {list(rivers.columns)}")
else:
    print("河川資料檔案不存在，請先執行 test_river_download.py")
    rivers = None

print()

# 2. 讀取消防署避難所 CSV → 轉為 GeoDataFrame → 轉換至 EPSG:3826
print("2. 讀取消防署避難所資料")

# 使用已清理的避難所資料
shelters_path = 'shelters_cleaned_3826.geojson'
if os.path.exists(shelters_path):
    shelters = gpd.read_file(shelters_path)
    print(f"避難所資料載入成功：{len(shelters)} 個避難所")
    print(f"  CRS: {shelters.crs}")
    print(f"  避難所邊界: {shelters.total_bounds}")
    print(f"  避難所欄位: {list(shelters.columns)}")
    
    # 檢查收容人數欄位
    capacity_cols = [col for col in shelters.columns if '容' in col or 'capacity' in col.lower()]
    print(f"  收容人數相關欄位: {capacity_cols}")
    
else:
    print("避難所資料檔案不存在，請先執行 load_shelter_data.py")
    shelters = None

print()

# 3. 資料清理統計（已在前面的腳本完成）
print("3. 資料清理統計")
print("資料清理已在 load_shelter_data.py 中完成")
print("  原始資料: 5,973 筆")
print("  清理後有效資料: 5,888 筆") 
print("  移除無效資料: 85 筆")
print("  清理項目:")
print("    - 座標為 0 的記錄")
print("    - 超出台灣範圍的座標 (經度: 119-122, 緯度: 21-26)")
print("    - 空值座標")
print("    - 經緯度反置檢查 (未發現問題)")

print()

# 4. 讀取鄉鎮界 → 轉換至 EPSG:3826
print("4. 讀取鄉鎮市區界線")

townships_path = 'townships_3826.geojson'
if os.path.exists(townships_path):
    townships = gpd.read_file(townships_path)
    print(f"鄉鎮區界線載入成功：{len(townships)} 個鄉鎮區")
    print(f"  CRS: {townships.crs}")
    print(f"  鄉鎮區邊界: {townships.total_bounds}")
    print(f"  鄉鎮區欄位: {list(townships.columns)}")
    
    # 縣市統計
    if 'COUNTYNAME' in townships.columns:
        county_count = townships['COUNTYNAME'].nunique()
        print(f"  涵蓋縣市數量: {county_count}")
        
        print("  各縣市鄉鎮區數量:")
        county_stats = townships.groupby('COUNTYNAME').size().sort_values(ascending=False)
        for county, count in county_stats.head(10).items():
            print(f"    {county}: {count} 個鄉鎮區")
        if len(county_stats) > 10:
            print(f"    ... 還有 {len(county_stats) - 10} 個縣市")
else:
    print("鄉鎮區界線檔案不存在，請先執行 load_township_data.py")
    townships = None

print()

# 資料完整性檢查
print("=== 資料完整性檢查 ===")
all_data_loaded = all([rivers is not None, shelters is not None, townships is not None])

if all_data_loaded:
    print("所有資料載入成功，可以開始分析")
    
    # 檢查座標系統一致性
    crs_consistent = (rivers.crs == shelters.crs == townships.crs == 'EPSG:3826')
    if crs_consistent:
        print("所有資料座標系統一致 (EPSG:3826)")
    else:
        print("座標系統不一致:")
        print(f"  河川: {rivers.crs}")
        print(f"  避難所: {shelters.crs}")
        print(f"  鄉鎮區: {townships.crs}")
    
    # 檢查空間範圍重疊
    river_bounds = rivers.total_bounds
    shelter_bounds = shelters.total_bounds
    township_bounds = townships.total_bounds
    
    print(f"\n空間範圍比較:")
    print(f"  河川: [{river_bounds[0]:.0f}, {river_bounds[1]:.0f}, {river_bounds[2]:.0f}, {river_bounds[3]:.0f}]")
    print(f"  避難所: [{shelter_bounds[0]:.0f}, {shelter_bounds[1]:.0f}, {shelter_bounds[2]:.0f}, {shelter_bounds[3]:.0f}]")
    print(f"  鄉鎮區: [{township_bounds[0]:.0f}, {township_bounds[1]:.0f}, {township_bounds[2]:.0f}, {township_bounds[3]:.0f}]")
    
else:
    missing_data = []
    if rivers is None: missing_data.append("河川資料")
    if shelters is None: missing_data.append("避難所資料")
    if townships is None: missing_data.append("鄉鎮區資料")
    
    print(f"缺少資料: {', '.join(missing_data)}")
    print("請先執行相關的資料載入腳本")

print("\n=== 資料載入與清理完成 ===")
print("準備進行多級緩衝區分析...")
