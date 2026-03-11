import geopandas as gpd
import folium
import pandas as pd
import matplotlib.pyplot as plt
import os

print("=== 視覺化分析 (Visualization) ===")
print()

# 載入所有必要的資料
print("載入視覺化資料...")

# 載入地理資料
rivers = gpd.read_file('river_data/riverpoly/riverpoly.shp')
if rivers.crs != 'EPSG:3826':
    rivers = rivers.to_crs('EPSG:3826')

buffer_high = gpd.read_file('buffer_high_risk.geojson')
buffer_med = gpd.read_file('buffer_med_risk.geojson')
buffer_low = gpd.read_file('buffer_low_risk.geojson')
shelters = gpd.read_file('shelters_with_risk_level.geojson')
townships = gpd.read_file('townships_3826.geojson')

print(f"河川資料：{len(rivers)} 個")
print(f"避難所資料：{len(shelters)} 個")
print(f"鄉鎮區資料：{len(townships)} 個")

# 1. 建立互動式風險地圖
print("\n1. 建立互動式風險地圖")

# 計算地圖中心點
bounds = shelters.total_bounds
center_lat = (bounds[1] + bounds[3]) / 2
center_lon = (bounds[0] + bounds[2]) / 2

# 轉換為 WGS84 用於 Folium
rivers_wgs84 = rivers.to_crs('EPSG:4326')
buffer_high_wgs84 = buffer_high.to_crs('EPSG:4326')
buffer_med_wgs84 = buffer_med.to_crs('EPSG:4326')
buffer_low_wgs84 = buffer_low.to_crs('EPSG:4326')
shelters_wgs84 = shelters.to_crs('EPSG:4326')
townships_wgs84 = townships.to_crs('EPSG:4326')

# 建立地圖
m = folium.Map(
    location=[center_lat, center_lon],
    zoom_start=8,
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

for idx, shelter in shelters_wgs84.iterrows():
    risk_level = shelter['risk_level']
    color = risk_colors.get(risk_level, '#808080')
    
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
    
    if '模擬收容人數' in shelter and pd.notna(shelter['模擬收容人數']):
        popup_info += f"收容人數：{int(shelter['模擬收容人數'])}人<br>"
    
    if 'risk_distance' in shelter and pd.notna(shelter['risk_distance']):
        popup_info += f"距離河川：{shelter['risk_distance']}公尺"
    
    folium.CircleMarker(
        location=[shelter.geometry.y, shelter.geometry.x],
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
map_file = 'risk_map_interactive.html'
m.save(map_file)
print(f"互動式風險地圖已儲存：{map_file}")

# 2. 建立 Top 10 風險區的長條圖
print("\n2. 建立 Top 10 風險區長條圖")

# 載入 Top 10 資料
top_10_data = pd.read_csv('top_10_risk_areas.csv', encoding='utf-8-sig')

# 設定中文字體
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft JhengHei']
plt.rcParams['axes.unicode_minus'] = False

# 建立圖表
fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(16, 12))
fig.suptitle('台灣河川洪災避難所風險分析', fontsize=18, fontweight='bold')

# 圖1：高風險避難所數量
top_10_sorted = top_10_data.sort_values('high_count', ascending=False)
area_names = [f"{row['COUNTYNAME']} {row['TOWNNAME']}" for _, row in top_10_sorted.iterrows()]

bars1 = ax1.barh(range(len(top_10_sorted)), top_10_sorted['high_count'], 
                 color='#FF4444', alpha=0.8)
ax1.set_yticks(range(len(top_10_sorted)))
ax1.set_yticklabels(area_names, fontsize=9)
ax1.set_xlabel('高風險避難所數量', fontsize=12)
ax1.set_title('Top 10 高風險行政區', fontsize=14, fontweight='bold')
ax1.grid(axis='x', alpha=0.3)

# 添加數值標籤
for i, v in enumerate(top_10_sorted['high_count']):
    ax1.text(v + 0.5, i, str(int(v)), va='center', fontsize=8)

# 圖2：風險總評分
bars2 = ax2.barh(range(len(top_10_sorted)), top_10_sorted['risk_score'], 
                 color='#FF8800', alpha=0.8)
ax2.set_yticks(range(len(top_10_sorted)))
ax2.set_yticklabels(area_names, fontsize=9)
ax2.set_xlabel('風險評分', fontsize=12)
ax2.set_title('Top 10 風險評分', fontsize=14, fontweight='bold')
ax2.grid(axis='x', alpha=0.3)

# 添加數值標籤
for i, v in enumerate(top_10_sorted['risk_score']):
    ax2.text(v + 2, i, f'{v:.1f}', va='center', fontsize=8)

# 圖3：風險等級分布圓餅圖
risk_totals = shelters['risk_level'].value_counts()
colors_risk = ['#FF4444', '#FF8800', '#FFD700', '#00C851']
labels_risk = ['高風險', '中風險', '低風險', '安全']

wedges, texts, autotexts = ax3.pie(risk_totals.values, 
                                  labels=labels_risk,
                                  colors=colors_risk,
                                  autopct='%1.1f%%',
                                  startangle=90,
                                  textprops={'fontsize': 10})
ax3.set_title('全台避難所風險分布', fontsize=14, fontweight='bold')

# 圖4：安全vs風險收容人數
if '模擬收容人數' in shelters.columns:
    safe_capacity = shelters[shelters['risk_level'] == 'safe']['模擬收容人數'].sum()
    risk_capacity = shelters[shelters['risk_level'] != 'safe']['模擬收容人數'].sum()
    
    capacity_data = [safe_capacity, risk_capacity]
    capacity_labels = [f'安全區\n{safe_capacity:,.0f}人', f'風險區\n{risk_capacity:,.0f}人']
    capacity_colors = ['#00C851', '#FF4444']
    
    ax4.pie(capacity_data, labels=capacity_labels, colors=capacity_colors, 
              autopct='%1.1f%%', startangle=90, textprops={'fontsize': 10})
    ax4.set_title('安全區 vs 風險區收容分布', fontsize=14, fontweight='bold')
else:
    ax4.text(0.5, 0.5, '收容人數資料不可用', ha='center', va='center', transform=ax4.transAxes)
    ax4.set_title('收容人數分布', fontsize=14, fontweight='bold')

plt.tight_layout()
chart_file = 'risk_analysis_charts.png'
plt.savefig(chart_file, dpi=300, bbox_inches='tight', facecolor='white', edgecolor='none')
print(f"統計圖表已儲存：{chart_file}")

plt.show()

# 3. 7. Export shelter_risk_audit.json
print("\n3. 匯出 shelter_risk_audit.json")

# 建立風險審計資料
shelter_audit = shelters[['risk_level']].copy()
shelter_audit['shelter_id'] = shelters.index

# 添加重要欄位
if '避難所名稱' in shelters.columns:
    shelter_audit['name'] = shelters['避難所名稱']
else:
    shelter_audit['name'] = '避難所_' + shelter_audit.index.astype(str)

# 檢查收容人數欄位
capacity_col = None
for col in shelters.columns:
    if '容納人數' in col or 'capacity' in col.lower():
        capacity_col = col
        break

if capacity_col and capacity_col in shelters.columns:
    shelter_audit['capacity'] = shelters[capacity_col]
else:
    shelter_audit['capacity'] = 0

if 'risk_distance' in shelters.columns:
    shelter_audit['distance_to_river'] = shelters['risk_distance']
else:
    shelter_audit['distance_to_river'] = None

# 添加座標資訊
shelters_wgs84_audit = shelters.to_crs('EPSG:4326')
shelter_audit['longitude'] = shelters_wgs84_audit.geometry.x
shelter_audit['latitude'] = shelters_wgs84_audit.geometry.y

# 重新排列欄位順序
shelter_audit = shelter_audit[[
    'shelter_id', 'name', 'risk_level', 'capacity', 
    'distance_to_river', 'longitude', 'latitude'
]]

# 匯出為 JSON
audit_file = 'shelter_risk_audit.json'
shelter_audit.to_json(audit_file, orient='records', indent=2, force_ascii=False)
print(f"避難所風險審計已匯出：{audit_file}")

# 4. 統計摘要
print("\n=== 視覺化分析完成 ===")
print(f"互動式地圖：{map_file}")
print(f"統計圖表：{chart_file}")
print(f"風險審計：{audit_file}")

print(f"\n資料摘要：")
print(f"- 總避難所數：{len(shelters)}")
print(f"- 高風險：{len(shelters[shelters['risk_level'] == 'high'])}")
print(f"- 中風險：{len(shelters[shelters['risk_level'] == 'medium'])}")
print(f"- 低風險：{len(shelters[shelters['risk_level'] == 'low'])}")
print(f"- 安全：{len(shelters[shelters['risk_level'] == 'safe'])}")

if capacity_col and capacity_col in shelters.columns:
    print(f"- 總收容人數：{shelters[capacity_col].sum():,.0f}")
else:
    print("- 收容人數：資料不可用")

print("\n=== 所有交付成果完成 ===")
print("互動式風險地圖 (risk_map_interactive.html)")
print("Top 10 統計圖表 (risk_analysis_charts.png)")
print("避難所風險審計 (shelter_risk_audit.json)")
print("完整分析流程完成！")
