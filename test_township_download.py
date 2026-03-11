import geopandas as gpd
from urllib.parse import quote
import requests
import zipfile
import io

# 測試鄉鎮市區界線下載
print("測試鄉鎮市區界線下載...")

url = 'https://www.tgos.tw/tgos/VirtualDir/Product/3fe61d4a-ca23-4f45-8aca-4a536f40f290/' + quote('鄉(鎮、市、區)界線1140318.zip')

print(f"URL: {url}")

try:
    # 嘗試直接讀取
    print("嘗試直接讀取...")
    townships = gpd.read_file(url)
    print(f"成功載入！鄉鎮區數量：{len(townships)}")
    print(f"CRS: {townships.crs}")
    print(f"欄位：{list(townships.columns)}")
    
except Exception as e:
    print(f"直接讀取失敗：{e}")
    
    try:
        # 嘗試下載後讀取
        print("嘗試下載後讀取...")
        response = requests.get(url)
        print(f"下載狀態：{response.status_code}")
        print(f"檔案大小：{len(response.content)} bytes")
        
        if response.status_code == 200:
            # 解壓縮並讀取
            with zipfile.ZipFile(io.BytesIO(response.content)) as zip_ref:
                print("壓縮檔內容：")
                for file in zip_ref.namelist():
                    print(f"  - {file}")
                
                # 尋找.shp檔案
                shp_files = [f for f in zip_ref.namelist() if f.endswith('.shp')]
                if shp_files:
                    print(f"找到shapefile：{shp_files[0]}")
                    
                    # 解壓縮到記憶體並讀取
                    zip_ref.extractall('township_temp')
                    
                    # 讀取shapefile
                    import os
                    for root, dirs, files in os.walk('township_temp'):
                        for file in files:
                            if file.endswith('.shp'):
                                shp_path = os.path.join(root, file)
                                townships = gpd.read_file(shp_path)
                                print(f"成功載入！鄉鎮區數量：{len(townships)}")
                                print(f"CRS: {townships.crs}")
                                print(f"欄位：{list(townships.columns)}")
                                
                                # 轉換為EPSG:3826
                                if townships.crs != 'EPSG:3826':
                                    townships = townships.to_crs('EPSG:3826')
                                    print(f"轉換為EPSG:3826：{townships.crs}")
                                
                                # 儲存檔案
                                townships.to_file('townships.geojson', driver='GeoJSON')
                                print("已儲存為 townships.geojson")
                                break
                else:
                    print("未找到shapefile檔案")
        else:
            print(f"下載失敗：HTTP {response.status_code}")
            
    except Exception as e2:
        print(f"下載讀取也失敗：{e2}")

print("\n=== 鄉鎮區資訊 ===")
if 'townships' in locals():
    print(f"總鄉鎮區數：{len(townships)}")
    print(f"邊界範圍：{townships.total_bounds}")
    
    # 顯示前幾個鄉鎮區的名稱
    if 'TOWNNAME' in townships.columns:
        print("前10個鄉鎮區：")
        for i, name in enumerate(townships['TOWNNAME'].head(10)):
            print(f"  {i+1}. {name}")
    elif 'COUNTYNAME' in townships.columns:
        print("縣市欄位存在，顯示前10個：")
        for i, name in enumerate(townships['COUNTYNAME'].head(10)):
            print(f"  {i+1}. {name}")
    
    # 顯示所有欄位
    print("所有欄位：")
    for col in townships.columns:
        print(f"  - {col}")
else:
    print("無法載入鄉鎮區資料")
