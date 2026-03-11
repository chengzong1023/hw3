import pandas as pd
import geopandas as gpd

# 載入清理後的避難所資料
shelters = gpd.read_file('shelters_cleaned.geojson')

print("=== 檢查經緯度反置問題 ===")
print(f"總避難所數量：{len(shelters)}")

# 檢查經緯度範圍是否合理
print(f"\n經度範圍：{shelters.geometry.x.min():.6f} ~ {shelters.geometry.x.max():.6f}")
print(f"緯度範圍：{shelters.geometry.y.min():.6f} ~ {shelters.geometry.y.max():.6f}")

# 檢查是否有經緯度反置的情況
# 正常情況：台灣經度約 119-122，緯度約 21-26
# 反置情況：經度會在 21-26，緯度會在 119-122

suspicious_points = []
for idx, point in shelters.geometry.items():
    lon, lat = point.x, point.y
    
    # 檢查是否可能反置
    if (21 <= lon <= 26) and (119 <= lat <= 122):
        suspicious_points.append({
            'index': idx,
            'original_lon': lon,
            'original_lat': lat,
            'swapped_lon': lat,
            'swapped_lat': lon,
            'name': shelters.iloc[idx].get('避難所名稱', 'N/A'),
            'address': shelters.iloc[idx].get('避難所地址', 'N/A')
        })

print(f"\n可能經緯度反置的點：{len(suspicious_points)} 個")

if suspicious_points:
    print("\n前10個可疑點：")
    for i, point in enumerate(suspicious_points[:10]):
        print(f"{i+1}. {point['name']}")
        print(f"   地址：{point['address']}")
        print(f"   原始：({point['original_lon']:.6f}, {point['original_lat']:.6f})")
        print(f"   交換後：({point['swapped_lon']:.6f}, {point['swapped_lat']:.6f})")
        print()

# 檢查座標為0的點（應該已經被清理掉了）
zero_points = shelters[(shelters.geometry.x == 0) | (shelters.geometry.y == 0)]
print(f"座標為0的點：{len(zero_points)} 個")

# 檢查空值
null_points = shelters[shelters.geometry.isna()]
print(f"空值座標點：{len(null_points)} 個")

# 生成報告
print("\n=== 座標品質報告 ===")
print(f"有效座標點：{len(shelters) - len(suspicious_points) - len(zero_points) - len(null_points)}")
print(f"可能經緯度反置：{len(suspicious_points)}")
print(f"座標為0：{len(zero_points)}")
print(f"空值座標：{len(null_points)}")

if suspicious_points:
    print(f"\n建議：檢查並修正 {len(suspicious_points)} 個可能的經緯度反置點")
    print("修正方法：交換經緯度座標值")
else:
    print("\n未發現明顯的經緯度反置問題")
