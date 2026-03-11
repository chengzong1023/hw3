import geopandas as gpd
import folium
import pandas as pd
import os

print("=== 修正互動式風險地圖 ===")
print()

# 載入所有必要的資料
print("載入地理資料...")

# 載入地理資料（確保使用 EPSG:3826）
rivers = gpd.read_file('river_data/riverpoly/riverpoly.shp')
if rivers.crs != 'EPSG:3826':
    rivers = rivers.to_crs('EPSG:3826')

buffer_high = gpd.read_file('buffer_high_risk.geojson')
buffer_med = gpd.read_file('buffer_med_risk.geojson')
buffer_low = gpd.read_file('buffer_low_risk.geojson')
shelters = gpd.read_file('shelters_with_risk_level.geojson')
townships = gpd.read_file('townships_3826.geojson')

print(f"河川資料：{len(rivers)} 個 (CRS: {rivers.crs})")
print(f"避難所資料：{len(shelters)} 個 (CRS: {shelters.crs})")
print(f"鄉鎮區資料：{len(townships)} 個 (CRS: {townships.crs})")

# 檢查座標範圍
print(f"\n座標範圍檢查：")
print(f"避難所邊界: {shelters.total_bounds}")
print(f"河川邊界: {rivers.total_bounds}")
print(f"鄉鎮區邊界: {townships.total_bounds}")

# 轉換為 WGS84 用於 Folium
print("\n轉換為 WGS84 座標系...")
rivers_wgs84 = rivers.to_crs('EPSG:4326')
buffer_high_wgs84 = buffer_high.to_crs('EPSG:4326')
buffer_med_wgs84 = buffer_med.to_crs('EPSG:4326')
buffer_low_wgs84 = buffer_low.to_crs('EPSG:4326')
shelters_wgs84 = shelters.to_crs('EPSG:4326')
townships_wgs84 = townships.to_crs('EPSG:4326')

print(f"WGS84 避難所邊界: {shelters_wgs84.total_bounds}")

# 計算台灣地圖中心點
# 台灣大約中心：經度 120.5, 緯度 23.8
center_lat = 23.8
center_lon = 120.5

print(f"地圖中心點：緯度 {center_lat}, 經度 {center_lon}")

# 建立地圖
print("\n建立互動式地圖...")
m = folium.Map(
    location=[center_lat, center_lon],
    zoom_start=7,
    tiles='OpenStreetMap'
)

# 添加三級緩衝區（從大到小，避免覆蓋）
# 低風險區（最外層）
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

# 中風險區
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

# 高風險區（最內層）
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

# 添加避難所點位（依風險等級著色）
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

for idx, shelter in shelters_wgs84.iterrows():
    risk_level = shelter['risk_level']
    color = risk_colors.get(risk_level, '#808080')
    
    # 檢查座標是否合理
    lon, lat = shelter.geometry.x, shelter.geometry.y
    if not (119 <= lon <= 122 and 21 <= lat <= 26):
        continue  # 跳過異常座標
    
    # 建立彈出式資訊
    popup_info = f"""
    <b>避難所資訊</b><br>
    風險等級：{risk_labels.get(risk_level, '未知')}<br>
    """
    
    # 添加其他可用資訊
    if '避難所名稱' in shelter and pd.notna(shelter['避難所名稱']):
        popup_info += f"名稱：{shelter['避難所名稱']}<br>"
    
    if '避難所地址' in shelter and pd.notna(shelter['避難所地址']):
        popup_info += f"地址：{shelter['避難所地址']}<br>"
    
    # 檢查收容人數欄位
    capacity_col = None
    for col in shelter.index:
        if '容納人數' in str(col) or 'capacity' in str(col).lower():
            capacity_col = col
            break
    
    if capacity_col and pd.notna(shelter[capacity_col]):
        popup_info += f"收容人數：{int(shelter[capacity_col])}人<br>"
    
    if 'risk_distance' in shelter and pd.notna(shelter['risk_distance']):
        popup_info += f"距離河川：{shelter['risk_distance']}公尺"
    
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
map_file = 'risk_map_interactive_fixed.html'
m.save(map_file)
print(f"修正後的互動式風險地圖已儲存：{map_file}")

# 統計各風險等級的避難所數量
risk_counts = shelters['risk_level'].value_counts()
print(f"\n避難所風險等級統計：")
for level, count in risk_counts.items():
    print(f"  {risk_labels.get(level, level)}：{count} 個")

print(f"\n地圖修正完成！")
print(f"檔案：{map_file}")
print(f"請在瀏覽器中開啟查看台灣地圖")
