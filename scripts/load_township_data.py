import geopandas as gpd
from urllib.parse import quote

# 載入鄉鎮市區界線資料
print("載入鄉鎮市區界線資料...")

url = 'https://www.tgos.tw/tgos/VirtualDir/Product/3fe61d4a-ca23-4f45-8aca-4a536f40f290/' + quote('鄉(鎮、市、區)界線1140318.zip')

try:
    # 指定圖層參數，避免多圖層警告
    townships = gpd.read_file(url, layer='TOWN_MOI_1140318')
    
    print(f"成功載入！鄉鎮區數量：{len(townships)}")
    print(f"原始 CRS: {townships.crs}")
    
    # 轉換為 EPSG:3826（與河川和避難所資料一致）
    if townships.crs != 'EPSG:3826':
        townships = townships.to_crs('EPSG:3826')
        print(f"轉換為 EPSG:3826: {townships.crs}")
    
    print(f"邊界範圍 (EPSG:3826): {townships.total_bounds}")
    
    # 顯示資料結構
    print(f"\n=== 資料結構 ===")
    print(f"欄位：{list(townships.columns)}")
    
    # 顯示縣市和鄉鎮區統計
    if 'COUNTYNAME' in townships.columns and 'TOWNNAME' in townships.columns:
        county_count = townships['COUNTYNAME'].nunique()
        town_count = len(townships)
        print(f"縣市數量：{county_count}")
        print(f"鄉鎮區數量：{town_count}")
        
        print(f"\n=== 縣市列表 ===")
        counties = townships['COUNTYNAME'].unique()
        for county in sorted(counties):
            town_count_in_county = len(townships[townships['COUNTYNAME'] == county])
            print(f"{county}：{town_count_in_county} 個鄉鎮區")
        
        print(f"\n=== 前10個鄉鎮區 ===")
        for i, (idx, row) in enumerate(townships.head(10).iterrows()):
            print(f"{i+1}. {row['COUNTYNAME']} {row['TOWNNAME']}")
    
    # 儲存檔案
    townships.to_file('townships_3826.geojson', driver='GeoJSON')
    print(f"\n已儲存為：townships_3826.geojson")
    
    # 檢查與其他資料的空間一致性
    print(f"\n=== 空間一致性檢查 ===")
    
    # 載入避難所資料進行比較
    try:
        shelters = gpd.read_file('shelters_cleaned_3826.geojson')
        print(f"避難所邊界：{shelters.total_bounds}")
        
        # 檢查避難所是否都在鄉鎮區範圍內
        shelters_in_townships = gpd.sjoin(shelters, townships, how='inner', predicate='within')
        coverage_rate = len(shelters_in_townships) / len(shelters) * 100
        print(f"避難所在鄉鎮區內的比例：{coverage_rate:.1f}% ({len(shelters_in_townships)}/{len(shelters)})")
        
        if coverage_rate < 95:
            print("警告：部分避難所不在鄉鎮區範圍內，可能需要檢查座標系統")
        else:
            print("✓ 空間一致性良好")
            
    except Exception as e:
        print(f"無法載入避難所資料進行比較：{e}")
    
    print(f"\n=== 鄉鎮區資料載入完成 ===")
    print(f"可用於：分區統計、地圖背景、空間連接分析")
    
except Exception as e:
    print(f"載入失敗：{e}")
    print("建議檢查網路連線或嘗試手動下載檔案")
