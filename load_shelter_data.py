import pandas as pd
import geopandas as gpd

# 載入避難所資料（從專案目錄）
data_path = r'data\避難收容處所點位檔案v9.csv'

print("載入避難所資料...")
try:
    # 嘗試 UTF-8 編碼
    shelters_csv = pd.read_csv(data_path, encoding='utf-8')
    print("使用 UTF-8 編碼成功載入")
except UnicodeDecodeError:
    try:
        # 嘗試 Big5 編碼
        shelters_csv = pd.read_csv(data_path, encoding='big5')
        print("使用 Big5 編碼成功載入")
    except UnicodeDecodeError:
        # 嘗試其他編碼
        shelters_csv = pd.read_csv(data_path, encoding='gbk')
        print("使用 GBK 編碼成功載入")

print(f"原始資料筆數：{len(shelters_csv)}")
print(f"資料欄位：{list(shelters_csv.columns)}")
print("\n前5筆資料：")
print(shelters_csv.head())

# 檢查座標欄位
print("\n=== 檢查座標欄位 ===")
for col in shelters_csv.columns:
    if '經' in col or '緯' in col or 'lon' in col.lower() or 'lat' in col.lower():
        print(f"找到可能的座標欄位：{col}")
        print(f"  - 資料類型：{shelters_csv[col].dtype}")
        print(f"  - 唯一值數量：{shelters_csv[col].nunique()}")
        print(f"  - 前5個值：{shelters_csv[col].head().tolist()}")

# 嘗試識別經緯度欄位
lon_col = None
lat_col = None

# 常見的經緯度欄位名稱
possible_lon = ['經度', 'lon', 'longitude', 'X', 'x座標', '橫坐標']
possible_lat = ['緯度', 'lat', 'latitude', 'Y', 'y座標', '縱坐標']

for col in shelters_csv.columns:
    col_lower = col.lower().replace(' ', '')
    for pl in possible_lon:
        if pl in col or pl.lower() in col_lower:
            lon_col = col
            break
    for pl in possible_lat:
        if pl in col or pl.lower() in col_lower:
            lat_col = col
            break

print(f"\n識別的座標欄位：")
print(f"經度欄位：{lon_col}")
print(f"緯度欄位：{lat_col}")

if lon_col and lat_col:
    # 檢查座標值範圍
    print(f"\n=== 座標值統計 ===")
    print(f"經度範圍：{shelters_csv[lon_col].min()} ~ {shelters_csv[lon_col].max()}")
    print(f"緯度範圍：{shelters_csv[lat_col].min()} ~ {shelters_csv[lat_col].max()}")
    
    # 檢查異常值
    print(f"\n=== 異常值檢查 ===")
    invalid_lon = (shelters_csv[lon_col] == 0) | (shelters_csv[lon_col].isna())
    invalid_lat = (shelters_csv[lat_col] == 0) | (shelters_csv[lat_col].isna())
    
    print(f"經度為0或空值：{invalid_lon.sum()} 筆")
    print(f"緯度為0或空值：{invalid_lat.sum()} 筆")
    
    # 檢查是否在台灣範圍內
    taiwan_bounds = {
        'lon_min': 119, 'lon_max': 122,
        'lat_min': 21, 'lat_max': 26
    }
    
    out_of_taiwan = (
        (shelters_csv[lon_col] < taiwan_bounds['lon_min']) | 
        (shelters_csv[lon_col] > taiwan_bounds['lon_max']) |
        (shelters_csv[lat_col] < taiwan_bounds['lat_min']) | 
        (shelters_csv[lat_col] > taiwan_bounds['lat_max'])
    )
    
    print(f"超出台灣範圍：{out_of_taiwan.sum()} 筆")
    
    # 資料清理
    print(f"\n=== 資料清理 ===")
    valid_shelters = shelters_csv[
        ~invalid_lon & ~invalid_lat & ~out_of_taiwan
    ].copy()
    
    print(f"清理後有效資料：{len(valid_shelters)} 筆")
    print(f"移除無效資料：{len(shelters_csv) - len(valid_shelters)} 筆")
    
    # 轉換為 GeoDataFrame
    shelters = gpd.GeoDataFrame(
        valid_shelters,
        geometry=gpd.points_from_xy(valid_shelters[lon_col], valid_shelters[lat_col]),
        crs='EPSG:4326'
    )
    
    print(f"\n=== GeoDataFrame 建立 ===")
    print(f"幾何欄位類型：{type(shelters.geometry)}")
    print(f"座標系統：{shelters.crs}")
    print(f"邊界：{shelters.total_bounds}")
    
    # 轉換為 EPSG:3826（台灣座標系）
    shelters_3826 = shelters.to_crs('EPSG:3826')
    print(f"\n轉換為 EPSG:3826 後邊界：{shelters_3826.total_bounds}")
    
    # 儲存清理後的資料
    shelters.to_file('shelters_cleaned.geojson', driver='GeoJSON')
    shelters_3826.to_file('shelters_cleaned_3826.geojson', driver='GeoJSON')
    print(f"\n清理後的資料已儲存為：")
    print(f"- shelters_cleaned.geojson (WGS84)")
    print(f"- shelters_cleaned_3826.geojson (EPSG:3826)")
    
else:
    print("\n無法識別經緯度欄位，請檢查資料欄位名稱")
