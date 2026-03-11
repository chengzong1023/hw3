import matplotlib.pyplot as plt
import pandas as pd
import geopandas as gpd
import os

print("=== 修正統計圖表 ===")
print()

# 設定中文字體
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft JhengHei']
plt.rcParams['axes.unicode_minus'] = False

# 載入資料
shelters = gpd.read_file('shelters_clean_with_risk.geojson')
top_10_data = pd.read_csv('top_10_risk_areas.csv', encoding='utf-8-sig')

print(f"避難所資料：{len(shelters)} 個")
print(f"Top 10 資料：{len(top_10_data)} 筆")

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

# 圖4：安全vs風險收容人數 - 修正版本
# 檢查收容人數欄位
capacity_col = None
for col in shelters.columns:
    if '容納人數' in str(col) or 'capacity' in str(col).lower():
        capacity_col = col
        break

if capacity_col:
    safe_capacity = shelters[shelters['risk_level'] == 'safe'][capacity_col].sum()
    risk_capacity = shelters[shelters['risk_level'] != 'safe'][capacity_col].sum()
    
    capacity_data = [safe_capacity, risk_capacity]
    capacity_labels = [f'安全區\n{safe_capacity:,.0f}人', f'風險區\n{risk_capacity:,.0f}人']
    capacity_colors = ['#00C851', '#FF4444']
    
    ax4.pie(capacity_data, labels=capacity_labels, colors=capacity_colors, 
              autopct='%1.1f%%', startangle=90, textprops={'fontsize': 10})
    ax4.set_title('安全區 vs 風險區收容分布', fontsize=14, fontweight='bold')
    
    print(f"收容人數統計：")
    print(f"  安全區收容：{safe_capacity:,.0f} 人")
    print(f"  風險區收容：{risk_capacity:,.0f} 人")
    print(f"  總收容人數：{safe_capacity + risk_capacity:,.0f} 人")
else:
    ax4.text(0.5, 0.5, '收容人數資料不可用', ha='center', va='center', 
             transform=ax4.transAxes, fontsize=12)
    ax4.set_title('收容人數分布', fontsize=14, fontweight='bold')

plt.tight_layout()
chart_file = 'risk_analysis_charts_fixed.png'
plt.savefig(chart_file, dpi=300, bbox_inches='tight', facecolor='white', edgecolor='none')
print(f"修正後的統計圖表已儲存：{chart_file}")

# 複製為 risk_map.png
import shutil
shutil.copy(chart_file, 'risk_map.png')
print(f"已複製為 risk_map.png")

plt.show()

print(f"\n=== 統計圖表修正完成 ===")
print(f"檔案：{chart_file}")
print(f"包含完整的收容人數分布圖表")
