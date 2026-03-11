import pandas as pd
import geopandas as gpd

print('檢查兩個避難所檔案...')

# 檢查避難所clean.csv
try:
    df1 = pd.read_csv('data/避難所clean.csv', encoding='utf-8')
    print(f'避難所clean.csv: {len(df1)} 筆記錄')
    print(f'欄位數量: {len(df1.columns)}')
    if '經度' in df1.columns and '緯度' in df1.columns:
        print(f'座標範圍 - 經度: {df1["經度"].min():.3f} ~ {df1["經度"].max():.3f}')
        print(f'座標範圍 - 緯度: {df1["緯度"].min():.3f} ~ {df1["緯度"].max():.3f}')
except Exception as e:
    print(f'避難所clean.csv 讀取失敗: {e}')

print()

# 檢查避難收容處所點位檔案v9.csv
try:
    df2 = pd.read_csv('data/避難收容處所點位檔案v9.csv', encoding='utf-8')
    print(f'避難收容處所點位檔案v9.csv: {len(df2)} 筆記錄')
    print(f'欄位數量: {len(df2.columns)}')
    if '經度' in df2.columns and '緯度' in df2.columns:
        print(f'座標範圍 - 經度: {df2["經度"].min():.3f} ~ {df2["經度"].max():.3f}')
        print(f'座標範圍 - 緯度: {df2["緯度"].min():.3f} ~ {df2["緯度"].max():.3f}')
except Exception as e:
    print(f'避難收容處所點位檔案v9.csv 讀取失敗: {e}')

print()
print('建議使用避難所clean.csv檔案進行分析')
