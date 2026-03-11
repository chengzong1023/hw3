import pandas as pd
import geopandas as gpd

print('=== 檢查 Week 3 作業要求 ===')
print()

# 1. 檢查安裝套件
print('1. 檢查安裝套件：')
try:
    import geopandas
    print(f'   geopandas: {geopandas.__version__}')
except ImportError:
    print('   geopandas: 未安裝')

try:
    import folium
    print(f'   folium: {folium.__version__}')
except ImportError:
    print('   folium: 未安裝')

try:
    import mapclassify
    print(f'   mapclassify: {mapclassify.__version__}')
except ImportError:
    print('   mapclassify: 未安裝')

try:
    import dotenv
    print(f'   python-dotenv: 已安裝')
except ImportError:
    print('   python-dotenv: 未安裝')

print()

# 2. 檢查河川資料
print('2. 檢查河川資料：')
rivers_url = 'https://gic.wra.gov.tw/Gis/gic/API/Google/DownLoad.aspx?fname=RIVERPOLY&filetype=SHP'

try:
    rivers = gpd.read_file(rivers_url)
    print(f'   河川資料載入成功：{len(rivers)} 個多邊形')
    print(f'   CRS：{rivers.crs}')
    
    if 'EPSG:3826' in str(rivers.crs):
        print('   ✓ 已為 EPSG:3826')
    else:
        print(f'   ⚠ 需要轉換為 EPSG:3826')
        
except Exception as e:
    print(f'   ✗ 河川資料載入失敗：{e}')
    print('   ⚠ 需要先下載解壓縮後再讀取')

print()

# 3. 檢查避難所 CSV
print('3. 檢查避難所 CSV：')
shelter_files = [
    'data/避難收容處所.csv',
    'data/避難所clean.csv',
    'data/避難收容處所點位檔案v9.csv'
]

for file_path in shelter_files:
    try:
        # 嘗試 UTF-8 編碼
        df = pd.read_csv(file_path, encoding='utf-8')
        print(f'   UTF-8 成功載入 {file_path}：{len(df)} 筆記錄')
        
        # 檢查座標欄位
        if '經度' in df.columns and '緯度' in df.columns:
            print(f'   座標欄位：經度、緯度')
            print(f'   經度範圍：{df["經度"].min():.3f} ~ {df["經度"].max():.3f}')
            print(f'   緯度範圍：{df["緯度"].min():.3f} ~ {df["緯度"].max():.3f}')
            
            # 檢查座標清理
            valid_coords = (
                (df['經度'] >= 119) & (df['經度'] <= 122) &
                (df['緯度'] >= 21) & (df['緯度'] <= 26) &
                (df['經度'] != 0) & (df['緯度'] != 0)
            )
            print(f'   有效座標：{valid_coords.sum()}/{len(df)} 筆')
            print(f'   清理後移除：{len(df) - valid_coords.sum()} 筆')
        break
        
    except UnicodeDecodeError:
        try:
            # 嘗試 Big5 編碼
            df = pd.read_csv(file_path, encoding='big5')
            print(f'   Big5 成功載入 {file_path}：{len(df)} 筆記錄')
            break
        except Exception as e:
            print(f'   載入失敗 {file_path}：{e}')
    except FileNotFoundError:
        print(f'   檔案不存在：{file_path}')
    except Exception as e:
        print(f'   其他錯誤 {file_path}：{e}')

print()

# 4. 檢查座標清理實作
print('4. 檢查座標清理實作：')
try:
    shelters = gpd.read_file('shelters_clean_with_real_capacity.geojson')
    print(f'   清理後避難所：{len(shelters)} 個')
    
    # 檢查座標範圍
    bounds = shelters.total_bounds
    print(f'   座標範圍：經度 {bounds[0]:.3f}~{bounds[2]:.3f}, 緯度 {bounds[1]:.3f}~{bounds[3]:.3f}')
    
    if (119 <= bounds[0] <= 122 and 119 <= bounds[2] <= 122 and 
        21 <= bounds[1] <= 26 and 21 <= bounds[3] <= 26):
        print('   ✓ 座標範圍正確')
    else:
        print('   ⚠ 座標範圍可能需要調整')
        
except Exception as e:
    print(f'   ✗ 檢查失敗：{e}')

print()

# 5. 檢查一對多 sjoin 實作
print('5. 檢查一對多 sjoin 實作：')
try:
    shelters = gpd.read_file('shelters_clean_with_real_capacity.geojson')
    risk_counts = shelters['risk_level'].value_counts()
    print(f'   風險等級分配：')
    for level, count in risk_counts.items():
        print(f'     {level}: {count} 個')
    
    # 檢查是否有階層式風險分配
    if 'high' in risk_counts and 'medium' in risk_counts and 'low' in risk_counts and 'safe' in risk_counts:
        print('   ✓ 已實作階層式風險分配（高 > 中 > 低 > 安全）')
    else:
        print('   ⚠ 風險分配可能不完整')
        
except Exception as e:
    print(f'   ✗ 檢查失敗：{e}')

print()
print('=== 檢查完成 ===')
