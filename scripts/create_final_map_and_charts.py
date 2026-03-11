import geopandas as gpd
import folium
import pandas as pd
import matplotlib.pyplot as plt
import os

print("=== 使用真實收容人數重新建立互動式地圖和統計圖表 ===")
print()

# 載入修正後的避難所資料（包含真實收容人數）
shelters = gpd.read_file('shelters_clean_with_real_capacity.geojson')
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
print("轉換為 WGS84 座標系...")
rivers_wgs84 = rivers.to_crs('EPSG:4326')
buffer_high_wgs84 = buffer_high.to_crs('EPSG:4326')
buffer_med_wgs84 = buffer_med.to_crs('EPSG:4326')
buffer_low_wgs84 = buffer_low.to_crs('EPSG:4326')
shelters_wgs84 = shelters.to_crs('EPSG:4326')
townships_wgs84 = townships.to_crs('EPSG:4326')

# 檢查收容人數欄位
capacity_col = None
for col in shelters.columns:
    if '容納人數' in str(col) or 'capacity' in str(col).lower():
        capacity_col = col
        break

print(f"找到收容人數欄位：{capacity_col}")
if capacity_col:
    print(f"收容人數統計：")
    print(f"  總收容人數：{shelters[capacity_col].sum():,.0f}")
    print(f"  平均收容人數：{shelters[capacity_col].mean():.1f}")
    print(f"  數值範圍：{shelters[capacity_col].min()} ~ {shelters[capacity_col].max()}")

# 建立互動式地圖
print("\n建立互動式地圖...")
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

# 添加避難所點位（包含真實收容人數）
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
    
    # 檢查座標是否存在且合理
    if shelter.geometry is None:
        continue
    
    lon, lat = shelter.geometry.x, shelter.geometry.y
    if pd.isna(lon) or pd.isna(lat):
        continue
    if not (119 <= lon <= 122 and 21 <= lat <= 26):
        continue  # 跳過異常座標
    
    # 建立詳細的彈出式資訊（包含真實收容人數）
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
    
    # 添加真實收容人數
    if capacity_col and pd.notna(shelter[capacity_col]):
        popup_info += f'<tr><td style="font-weight: bold; padding: 5px;">收容人數：</td><td style="padding: 5px;">{int(shelter[capacity_col])} 人</td></tr>'
    else:
        popup_info += '<tr><td style="font-weight: bold; padding: 5px;">收容人數：</td><td style="padding: 5px;">無資料</td></tr>'
    
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
map_file = 'risk_map_final_with_real_capacity.html'
m.save(map_file)
print(f"互動式地圖已儲存：{map_file}")

# 複製為主要檔案
import shutil
shutil.copy(map_file, 'risk_map_interactive.html')
print(f"已複製為 risk_map_interactive.html")

# 建立統計圖表（使用真實收容人數）
print("\n建立統計圖表...")

# 設定中文字體
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft JhengHei']
plt.rcParams['axes.unicode_minus'] = False

# 載入 Top 10 資料
top_10_data = pd.read_csv('top_10_risk_areas.csv', encoding='utf-8-sig')

# 建立圖表
fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(16, 12))
fig.suptitle('台灣河川洪災避難所風險分析（真實收容人數）', fontsize=18, fontweight='bold')

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

# 圖4：安全vs風險收容人數（使用真實資料）
if capacity_col:
    safe_capacity = shelters[shelters['risk_level'] == 'safe'][capacity_col].sum()
    risk_capacity = shelters[shelters['risk_level'] != 'safe'][capacity_col].sum()
    
    capacity_data = [safe_capacity, risk_capacity]
    capacity_labels = [f'安全區\n{safe_capacity:,.0f}人', f'風險區\n{risk_capacity:,.0f}人']
    capacity_colors = ['#00C851', '#FF4444']
    
    ax4.pie(capacity_data, labels=capacity_labels, colors=capacity_colors, 
              autopct='%1.1f%%', startangle=90, textprops={'fontsize': 10})
    ax4.set_title('安全區 vs 風險區收容分布（真實資料）', fontsize=14, fontweight='bold')
    
    print(f"真實收容人數統計：")
    print(f"  安全區收容：{safe_capacity:,.0f} 人")
    print(f"  風險區收容：{risk_capacity:,.0f} 人")
    print(f"  總收容人數：{safe_capacity + risk_capacity:,.0f} 人")
else:
    ax4.text(0.5, 0.5, '收容人數資料不可用', ha='center', va='center', 
             transform=ax4.transAxes, fontsize=12)
    ax4.set_title('收容人數分布', fontsize=14, fontweight='bold')

plt.tight_layout()
chart_file = 'risk_analysis_charts_real_capacity.png'
plt.savefig(chart_file, dpi=300, bbox_inches='tight', facecolor='white', edgecolor='none')
print(f"統計圖表已儲存：{chart_file}")

# 複製為主要檔案
shutil.copy(chart_file, 'risk_analysis_charts.png')
shutil.copy(chart_file, 'risk_map.png')
print(f"已複製為 risk_analysis_charts.png 和 risk_map.png")

plt.show()

# 統計資訊
risk_counts = shelters['risk_level'].value_counts()
print(f"\n=== 最終統計 ===")
print(f"避難所風險等級統計：")
for level, count in risk_counts.items():
    print(f"  {risk_labels.get(level, level)}：{count} 個")

print(f"\n=== 完成 ===")
print(f"互動式地圖：risk_map_interactive.html（包含真實收容人數）")
print(f"統計圖表：risk_analysis_charts.png（包含真實收容人數）")
print(f"靜態地圖：risk_map.png")
print("現在所有圖表都使用真實的收容人數資料！")
