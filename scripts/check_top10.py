import pandas as pd

# 檢查完整的 Top 10 資料
print("=== 檢查完整的 Top 10 風險區 ===")

# 讀取已儲存的資料
df = pd.read_csv('top_10_risk_areas.csv', encoding='utf-8-sig')

print(f"總記錄數：{len(df)}")
print("\n完整的 Top 10 風險行政區：")

for i, (idx, row) in enumerate(df.iterrows()):
    print(f"{i+1:2d}. {row['COUNTYNAME']} {row['TOWNNAME']}")
    print(f"     高風險:{int(row['high_count'])} 中風險:{int(row['medium_count'])} "
          f"低風險:{int(row['low_count'])} 安全:{int(row['safe_count'])}")
    print(f"     風險評分:{row['risk_score']:.1f}")
    print(f"     風險收容:{int(row['risk_capacity'])} 安全收容:{int(row['safe_capacity'])}")
    print()

print("=== 檢查高風險避難所排名 ===")
high_risk_sorted = df.sort_values('high_count', ascending=False)

print("高風險避難所最多的前10個鄉鎮區：")
for i, (idx, row) in enumerate(high_risk_sorted.iterrows()):
    print(f"{i+1:2d}. {row['COUNTYNAME']} {row['TOWNNAME']} - "
          f"高風險:{int(row['high_count'])}個, "
          f"總收容:{int(row['total_capacity'])}人")
