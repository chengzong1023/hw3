import geopandas as gpd
import pandas as pd
import matplotlib.pyplot as plt
import os

print("=== 收容量缺口分析 (Capacity Gap Analysis) ===")
print()

# 載入已分析的資料
print("載入分析資料...")

# 載入帶有風險等級的避難所資料
shelters = gpd.read_file('shelters_with_risk_level.geojson')
print(f"避難所資料：{len(shelters)} 個")

# 載入鄉鎮區資料
townships = gpd.read_file('townships_3826.geojson')
print(f"鄉鎮區資料：{len(townships)} 個")

print()

# 1. 分區統計：按鄉鎮市區彙總
print("1. 分區統計：按鄉鎮市區彙總")

# 將避難所與鄉鎮區進行空間連接
shelters_with_township = gpd.sjoin(shelters, townships, how='inner', predicate='within')
print(f"成功連接 {len(shelters_with_township)} 個避難所到鄉鎮區")

# 檢查收容人數欄位
capacity_col = None
for col in shelters.columns:
    if '容納人數' in col or 'capacity' in col.lower():
        capacity_col = col
        break

if capacity_col:
    print(f"使用收容人數欄位：{capacity_col}")
else:
    print("警告：未找到收容人數欄位，將使用模擬資料")
    # 創建模擬收容人數
    import numpy as np
    np.random.seed(42)
    capacity_col = '模擬收容人數'
    shelters[capacity_col] = np.random.randint(50, 500, size=len(shelters))
    print(f"已創建模擬收容人數（平均：{shelters[capacity_col].mean():.0f} 人）")

# 確保收容人數為數值型
shelters[capacity_col] = pd.to_numeric(shelters[capacity_col], errors='coerce').fillna(0)

print(f"收容人數欄位確認：{capacity_col}")
print(f"收容人數範圍：{shelters[capacity_col].min()} ~ {shelters[capacity_col].max()}")

# 按鄉鎮區和風險等級分組統計
print("進行分區統計...")

# 各區各風險等級的避難所數量和收容人數
township_stats = shelters_with_township.groupby(['COUNTYNAME', 'TOWNNAME', 'risk_level']).agg({
    'geometry': 'count',  # 避難所數量
}).reset_index()

# 重新命名欄位
township_stats.columns = ['COUNTYNAME', 'TOWNNAME', 'risk_level', 'shelter_count']

# 計算各組的收容人數
capacity_by_group = shelters_with_township.groupby(['COUNTYNAME', 'TOWNNAME', 'risk_level']).apply(
    lambda x: pd.Series({capacity_col: x[capacity_col].sum()})
).reset_index()

# 合併數量和收容人數
township_stats = township_stats.merge(capacity_by_group, on=['COUNTYNAME', 'TOWNNAME', 'risk_level'])

print(f"統計完成，共 {len(township_stats)} 條記錄")

# 建立樞紐表方便分析
print("建立詳細統計表...")

# 避難所數量統計
shelter_count_pivot = township_stats.pivot_table(
    index=['COUNTYNAME', 'TOWNNAME'],
    columns='risk_level',
    values='shelter_count',
    fill_value=0
).reset_index()

# 收容人數統計
capacity_pivot = township_stats.pivot_table(
    index=['COUNTYNAME', 'TOWNNAME'],
    columns='risk_level',
    values='total_capacity',
    fill_value=0
).reset_index()

# 合併統計
merged_stats = shelter_count_pivot.merge(
    capacity_pivot,
    on=['COUNTYNAME', 'TOWNNAME'],
    suffixes=('_count', '_capacity')
)

# 計算各區總計
merged_stats['total_shelters'] = merged_stats[['high_count', 'medium_count', 'low_count', 'safe_count']].sum(axis=1)
merged_stats['total_capacity'] = merged_stats[['high_capacity', 'medium_capacity', 'low_capacity', 'safe_capacity']].sum(axis=1)
merged_stats['risk_shelters'] = merged_stats[['high_count', 'medium_count', 'low_count']].sum(axis=1)
merged_stats['risk_capacity'] = merged_stats[['high_capacity', 'medium_capacity', 'low_capacity']].sum(axis=1)

print("鄉鎮區統計完成")

# 顯示前10個高風險鄉鎮區
print("\n高風險避難所最多的前10個鄉鎮區：")
top_10_high_risk = merged_stats.sort_values('high_count', ascending=False).head(10)
for i, (idx, row) in enumerate(top_10_high_risk.iterrows()):
    print(f"{i+1:2d}. {row['COUNTYNAME']} {row['TOWNNAME']:8s} - "
          f"高風險:{row['high_count']:3d}個, "
          f"總收容:{row['total_capacity']:5.0f}人")

print()

# 2. 缺口判斷
print("2. 缺口判斷分析")

# 計算安全指標
# 假設需要至少20%的總收容人在安全區域
SAFETY_RATIO = 0.2

merged_stats['safety_ratio'] = merged_stats['safe_capacity'] / merged_stats['total_capacity']
merged_stats['risk_ratio'] = merged_stats['risk_capacity'] / merged_stats['total_capacity']
merged_stats['has_capacity_gap'] = merged_stats['safety_ratio'] < SAFETY_RATIO

# 識別收容量不足的行政區
capacity_gap_areas = merged_stats[merged_stats['has_capacity_gap']].copy()
capacity_gap_areas = capacity_gap_areas.sort_values('risk_capacity', ascending=False)

print(f"安全區收容不足的行政區：{len(capacity_gap_areas)} 個")
print(f"（安全區收容量 < {SAFETY_RATIO*100:.0f}% 總收容量）")

print("\n收容量缺口最嚴重的前10個行政區：")
top_10_gaps = capacity_gap_areas.head(10)
for i, (idx, row) in enumerate(top_10_gaps.iterrows()):
    print(f"{i+1:2d}. {row['COUNTYNAME']} {row['TOWNNAME']:8s}")
    print(f"     風險區收容:{row['risk_capacity']:5.0f}人 "
          f"({row['risk_ratio']*100:.1f}%)")
    print(f"     安全區收容:{row['safe_capacity']:5.0f}人 "
          f"({row['safety_ratio']*100:.1f}%)")
    print(f"     缺口程度:{(SAFETY_RATIO-row['safety_ratio'])*100:+.1f}%")
    print()

# 3. 風險最高的 Top 10 行政區排名
print("3. 風險最高的 Top 10 行政區排名")

# 綜合風險評分：考慮高風險避難所數量和收容人數
merged_stats['risk_score'] = (
    merged_stats['high_count'] * 3 +          # 高風險權重 3
    merged_stats['medium_count'] * 2 +        # 中風險權重 2
    merged_stats['low_count'] * 1 +          # 低風險權重 1
    merged_stats['high_capacity'] / 100        # 收容人數因素
)

top_10_risk_areas = merged_stats.sort_values('risk_score', ascending=False).head(10)

print("風險最高的 Top 10 行政區：")
for i, (idx, row) in enumerate(top_10_risk_areas.iterrows()):
    print(f"{i+1:2d}. {row['COUNTYNAME']} {row['TOWNNAME']:8s} - "
          f"風險評分:{row['risk_score']:6.1f}")
    print(f"     高:{row['high_count']:3d} 中:{row['medium_count']:3d} "
          f"低:{row['low_count']:3d} 安全:{row['safe_count']:3d}")
    print(f"     風險收容:{row['risk_capacity']:5.0f}人 "
          f"安全收容:{row['safe_capacity']:5.0f}人")

# 4. 儲存分析結果
print("\n4. 儲存分析結果")

# 儲存詳細統計
merged_stats.to_csv('township_capacity_analysis.csv', index=False, encoding='utf-8-sig')
print("已儲存 township_capacity_analysis.csv")

# 儲存 Top 10 風險區
top_10_risk_areas.to_csv('top_10_risk_areas.csv', index=False, encoding='utf-8-sig')
print("已儲存 top_10_risk_areas.csv")

# 儲存收容量缺口區
capacity_gap_areas.to_csv('capacity_gap_areas.csv', index=False, encoding='utf-8-sig')
print("已儲存 capacity_gap_areas.csv")

# 5. 建立統計圖表
print("\n5. 建立統計圖表")

# 創建圖表
fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 12))
fig.suptitle('避難所收容量缺口分析', fontsize=16, fontproperties='SimHei')

# 圖1：Top 10 高風險區（避難所數量）
top_10_chart = top_10_risk_areas.copy()
top_10_chart['area_name'] = top_10_chart['COUNTYNAME'] + ' ' + top_10_chart['TOWNNAME']

ax1.barh(range(len(top_10_chart)), top_10_chart['high_count'], color='red', alpha=0.7)
ax1.set_yticks(range(len(top_10_chart)))
ax1.set_yticklabels(top_10_chart['area_name'], fontsize=8)
ax1.set_xlabel('高風險避難所數量')
ax1.set_title('Top 10 高風險行政區（避難所數量）')
ax1.grid(axis='x', alpha=0.3)

# 圖2：Top 10 高風險區（收容人數）
ax2.barh(range(len(top_10_chart)), top_10_chart['high_capacity'], color='orange', alpha=0.7)
ax2.set_yticks(range(len(top_10_chart)))
ax2.set_yticklabels(top_10_chart['area_name'], fontsize=8)
ax2.set_xlabel('高風險區收容人數')
ax2.set_title('Top 10 高風險行政區（收容人數）')
ax2.grid(axis='x', alpha=0.3)

# 圖3：收容量缺口區域
gap_chart = capacity_gap_areas.head(10).copy()
gap_chart['area_name'] = gap_chart['COUNTYNAME'] + ' ' + gap_chart['TOWNNAME']
gap_chart['gap_percentage'] = (SAFETY_RATIO - gap_chart['safety_ratio']) * 100

ax3.barh(range(len(gap_chart)), gap_chart['gap_percentage'], 
         color=['red' if x > 10 else 'orange' if x > 5 else 'yellow' for x in gap_chart['gap_percentage']], 
         alpha=0.7)
ax3.set_yticks(range(len(gap_chart)))
ax3.set_yticklabels(gap_chart['area_name'], fontsize=8)
ax3.set_xlabel('安全容量缺口百分比 (%)')
ax3.set_title('收容量缺口最嚴重區域')
ax3.grid(axis='x', alpha=0.3)

# 圖4：風險等級分布總覽
risk_totals = merged_stats[['high_count', 'medium_count', 'low_count', 'safe_count']].sum()
colors = ['red', 'orange', 'yellow', 'green']
ax4.pie(risk_totals, labels=['高風險', '中風險', '低風險', '安全'], 
         colors=colors, autopct='%1.1f%%', startangle=90)
ax4.set_title('全台避難所風險等級分布')

plt.tight_layout()
plt.savefig('capacity_gap_analysis.png', dpi=300, bbox_inches='tight', 
            facecolor='white', edgecolor='none')
print("已儲存 capacity_gap_analysis.png")

plt.show()

# 6. 總結報告
print("\n=== 收容量缺口分析完成 ===")
print(f"分析縣市數量：{merged_stats['COUNTYNAME'].nunique()} 個")
print(f"分析鄉鎮區數量：{len(merged_stats)} 個")
print(f"安全容量不足區域：{len(capacity_gap_areas)} 個 ({len(capacity_gap_areas)/len(merged_stats)*100:.1f}%)")
print(f"總避難所數量：{merged_stats['total_shelters'].sum()} 個")
print(f"總收容人數：{merged_stats['total_capacity'].sum():.0f} 人")
print(f"風險區收容：{merged_stats['risk_capacity'].sum():.0f} 人 ({merged_stats['risk_ratio'].mean()*100:.1f}%)")
print(f"安全區收容：{merged_stats['safe_capacity'].sum():.0f} 人 ({merged_stats['safety_ratio'].mean()*100:.1f}%)")

print("\n輸出檔案：")
print("- township_capacity_analysis.csv (詳細統計)")
print("- top_10_risk_areas.csv (Top 10 風險區)")
print("- capacity_gap_areas.csv (收容量缺口區)")
print("- capacity_gap_analysis.png (統計圖表)")

print("\n準備進行視覺化分析...")
