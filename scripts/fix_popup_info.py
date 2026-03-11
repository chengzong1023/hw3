import geopandas as gpd
import folium
import pandas as pd
import os

print("=== 修正避難所彈出式資訊 ===")
print()

# 載入清理後的避難所資料
shelters = gpd.read_file('shelters_clean_with_risk.geojson')
print(f"載入避難所資料：{len(shelters)} 個")

# 載入其他地理資料
rivers = gpd.read_file('river_data/riverpoly/riverpoly.shp')
if rivers.crs != 'EPSG:3826':
    rivers = rivers.to_crs('EPSG:3826')

buffer_high = gpd.read_file('buffer_high_risk.geojson')
buffer_med = gpd.read_file('buffer_med_risk.geojson')
buffer_low = gpd.read_file('buffer_low_risk.geojson')
townships = gpd.read_file('townships_3826.geojson')

# 轉換為 WGS84 用於 Folium
rivers_wgs84 = rivers.to_crs('EPSG:4326')
buffer_high_wgs84 = buffer_high.to_crs('EPSG:4326')
buffer_med_wgs84 = buffer_med.to_crs('EPSG:4326')
buffer_low_wgs84 = buffer_low.to_crs('EPSG:4326')
shelters_wgs84 = shelters.to_crs('EPSG:4326')
townships_wgs84 = townships.to_crs('EPSG:4326')

# 建立地圖
center_lat = 23.8
center_lon = 120.5

m = folium.Map(
    location=[center_lat, center_lon],
    zoom_start=7,
    tiles='OpenStreetMap'
)

# 添加三級緩衝區
folium.GeoJson(
    buffer_low_wgs84,
    style_function=lambda x: {
        'fillColor': '#FFFF00',  # 黃色
        'color': 'none',
        'fillOpacity': 0.2,
        'weight': 0
    },
    name='低風險區 (2km)',
    tooltip='低風險區 - 2公里緩衝區'
).add_to(m)

folium.GeoJson(
    buffer_med_wgs84,
    style_function=lambda x: {
        'fillColor': '#FFA500',  # 橙色
        'color': 'none',
        'fillOpacity': 0.3,
        'weight': 0
    },
    name='中風險區 (1km)',
    tooltip='中風險區 - 1公里緩衝區'
).add_to(m)

folium.GeoJson(
    buffer_high_wgs84,
    style_function=lambda x: {
        'fillColor': '#FF0000',  # 紅色
        'color': 'none',
        'fillOpacity': 0.4,
        'weight': 0
    },
    name='高風險區 (500m)',
    tooltip='高風險區 - 500公尺緩衝區'
).add_to(m)

# 添加河川面
folium.GeoJson(
    rivers_wgs84,
    style_function=lambda x: {
        'color': '#0066CC',  # 藍色
        'weight': 2,
        'fillOpacity': 0.7
    },
    name='河川',
    tooltip='河川'
).add_to(m)

# 添加鄉鎮區邊界
folium.GeoJson(
    townships_wgs84,
    style_function=lambda x: {
        'color': '#666666',  # 灰色
        'weight': 1,
        'fillOpacity': 0
    },
    name='鄉鎮區界線',
    tooltip='鄉鎮區界線'
).add_to(m)

# 添加避難所點位（修正彈出式資訊）
risk_colors = {
    'high': '#FF0000',    # 紅色
    'medium': '#FFA500',  # 橙色
    'low': '#FFFF00',     # 黃色
    'safe': '#00FF00'     # 綠色
}

risk_labels = {
    'high': '高風險',
    'medium': '中風險',
    'low': '低風險',
    'safe': '安全'
}

print(f"添加 {len(shelters_wgs84)} 個避難所點位...")

# 檢查避難所資料的實際欄位
print("避難所資料欄位：")
for col in shelters.columns:
    print(f"  - {col}")

for idx, shelter in shelters_wgs84.iterrows():
    risk_level = shelter['risk_level']
    color = risk_colors.get(risk_level, '#808080')
    
    # 檢查座標是否合理
    lon, lat = shelter.geometry.x, shelter.geometry.y
    if not (119 <= lon <= 122 and 21 <= lat <= 26):
        continue  # 跳過異常座標
    
    # 建立詳細的彈出式資訊
    popup_info = f"""
    <div style="width: 250px;">
    <h4 style="color: {color}; margin-bottom: 10px;">避難所資訊</h4>
    <table style="border-collapse: collapse; width: 100%;">
    <tr><td style="font-weight: bold; padding: 5px;">風險等級：</td><td style="padding: 5px;"><span style="color: {color}; font-weight: bold;">{risk_labels.get(risk_level, '未知')}</span></td></tr>
    """
    
    # 添加名稱
    if '避難所名稱' in shelter and pd.notna(shelter['避難所名稱']):
        popup_info += f'<tr><td style="font-weight: bold; padding: 5px;">名稱：</td><td style="padding: 5px;">{shelter["避難所名稱"]}</td></tr>'
    
    # 添加地址
    if '避難所地址' in shelter and pd.notna(shelter['避難所地址']):
        popup_info += f'<tr><td style="font-weight: bold; padding: 5px;">地址：</td><td style="padding: 5px;">{shelter["避難所地址"]}</td></tr>'
    
    # 檢查收容人數欄位
    capacity_value = "無資料"
    for col in shelter.index:
        if '容納人數' in str(col) or 'capacity' in str(col).lower():
            if pd.notna(shelter[col]):
                capacity_value = f"{int(shelter[col])} 人"
            break
    
    popup_info += f'<tr><td style="font-weight: bold; padding: 5px;">收容人數：</td><td style="padding: 5px;">{capacity_value}</td></tr>'
    
    # 添加風險距離
    if 'risk_distance' in shelter and pd.notna(shelter['risk_distance']):
        popup_info += f'<tr><td style="font-weight: bold; padding: 5px;">距離河川：</td><td style="padding: 5px;">{shelter["risk_distance"]} 公尺</td></tr>'
    
    # 添加座標
    popup_info += f'<tr><td style="font-weight: bold; padding: 5px;">座標：</td><td style="padding: 5px;">{lat:.6f}, {lon:.6f}</td></tr>'
    
    popup_info += """
    </table>
    </div>
    """
    
    folium.CircleMarker(
        location=[lat, lon],
        radius=5,
        popup=folium.Popup(popup_info, max_width=300),
        color=color,
        fill=True,
        fillColor=color,
        weight=2
    ).add_to(m)

# 添加圖層控制
folium.LayerControl().add_to(m)

# 儲存互動式地圖
map_file = 'risk_map_with_popup.html'
m.save(map_file)
print(f"修正後的互動式風險地圖已儲存：{map_file}")

# 統計各風險等級的避難所數量
risk_counts = shelters['risk_level'].value_counts()
print(f"\n避難所風險等級統計：")
for level, count in risk_counts.items():
    print(f"  {risk_labels.get(level, level)}：{count} 個")

print(f"\n=== 彈出式資訊修正完成 ===")
print(f"檔案：{map_file}")
print("現在點擊避難所會顯示完整的詳細資訊")
