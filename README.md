# 第3週作業：河川洪災避難所風險評估 (ARIA)

## 專案概述
自動化區域影響評估工具，用於分析台灣河川附近緊急避難所的洪災風險，使用水利署河川圖資和消防署避難所位置資料。

## 資料來源
- **河川資料**：水利署河川面圖資 (EPSG:3826)
- **避難所資料**：消防署緊急避難所 (data.gov.tw)
- **行政區界**：國土測繪中心鄉鎮市區界線

## 設定說明

### 1. 安裝相依套件
```bash
pip install -r requirements.txt
```

### 2. 下載避難所資料
1. 前往：https://data.gov.tw/dataset/73242
2. 下載緊急避難所 CSV 檔案
3. 專案目錄下儲存為 `data/避難收容處所.csv`

### 3. 執行分析
在 Jupyter 中開啟 `ARIA.ipynb` 並依序執行所有儲存格。

## 主要功能
- **多級風險區域**：500公尺（高）、1公里（中）、2公里（低）緩衝區
- **空間分析**：使用 `gpd.sjoin()` 識別風險區內的避難所
- **收容量缺口分析**：完整實作安全避難所總收容量 vs 風險區需求分析，包含容量缺口比率計算
- **綜合風險評分**：基於風險等級、避難所數量和容量缺口的加權評分系統
- **互動式視覺化**：使用 Folium 製作依風險等級著色的地圖
- **自動化報告**：匯出避難所風險評估 JSON 檔案

## 交付成果
- `ARIA.ipynb` - 完整分析筆記本
- `shelter_risk_audit.json` - 避難所風險分類
- `risk_map.png` - 靜態風險地圖或統計圖
- `top_10_risk_areas.csv` - 詳細收容量缺口分析
- `interactive_map.zip` - 互動式風險地圖（壓縮檔）
- `interactive_map_info.txt` - 互動式地圖使用說明

## AI 診斷日誌

### 遇到的問題與解決方案

#### 問題1：直接讀取 WRA URL 失敗
**問題**：`gpd.read_file()` 無法直接讀取 WRA URL，因為 zip 格式處理問題
**解決方案**：先下載 zip 檔案，解壓縮後再從子目錄讀取 shapefile
**程式碼修正**：
```python
# 不要直接讀取：
rivers = gpd.read_file(url)

# 改用這種方法：
r = requests.get(url)
with zipfile.ZipFile(io.BytesIO(r.content)) as zip_ref:
    zip_ref.extractall('temp')
rivers = gpd.read_file('temp/riverpoly/riverpoly.shp')
```

#### 問題2：Shapefile 路徑解析
**問題**：Shapefile 位於巢狀子目錄（`riverpoly/riverpoly.shp`）
**解決方案**：使用 `os.walk()` 遞迴尋找 .shp 檔案
**程式碼修正**：
```python
shp_files = []
for root, dirs, files in os.walk('river_data'):
    for file in files:
        if file.endswith('.shp'):
            shp_files.append(os.path.join(root, file))
```

#### 問題3：PowerShell 指令語法
**問題**：PowerShell 不支援像 bash 的 `&&` 運算子
**解決方案**：使用分開的指令或正確的 PowerShell 語法

#### 問題4：互動式地圖座標範圍錯誤
**問題**：互動式地圖顯示不在台灣範圍，座標計算錯誤
**解決方案**：重新計算台灣中心點（緯度 23.8, 經度 120.5），檢查座標範圍合理性
**程式碼修正**：
```python
# 設定正確的台灣中心點
center_lat = 23.8
center_lon = 120.5

# 檢查座標範圍
if not (119 <= lon <= 122 and 21 <= lat <= 26):
    continue  # 跳過異常座標
```

#### 問題5：避難所收容人數資料遺失
**問題**：CSV 轉換到 GeoJSON 時，`可容納人數` 欄位遺失，圖表顯示「資料不可用」
**解決方案**：重新轉換 CSV 到 GeoJSON，確保收容人數欄位正確傳遞
**程式碼修正**：
```python
# 檢查收容人數欄位
capacity_col = None
for col in shelters.columns:
    if '容納人數' in str(col) or 'capacity' in str(col).lower():
        capacity_col = col
        break

# 確保欄位存在於 GeoJSON
if capacity_col:
    shelters_gdf[capacity_col] = shelters_csv[capacity_col]
```

#### 問題6：彈出式資訊不完整
**問題**：點擊避難所時，彈出式資訊缺少收容人數等詳細資料
**解決方案**：重新設計彈出式視窗，使用表格格式顯示完整資訊
**程式碼修正**：
```python
popup_info = f"""
<div style="width: 250px;">
<h4 style="color: {color}; margin-bottom: 10px;">避難所資訊</h4>
<table style="border-collapse: collapse; width: 100%;">
<tr><td style="font-weight: bold; padding: 5px;">風險等級：</td><td style="padding: 5px;">{risk_labels.get(risk_level, '未知')}</td></tr>
<tr><td style="font-weight: bold; padding: 5px;">名稱：</td><td style="padding: 5px;">{shelter['避難所名稱']}</td></tr>
<tr><td style="font-weight: bold; padding: 5px;">收容人數：</td><td style="padding: 5px;">{int(shelter[capacity_col])} 人</td></tr>
</table>
</div>
"""
```

#### 問題7：Unicode 編碼錯誤
**問題**：Python 輸出中文時出現 `UnicodeEncodeError`
**解決方案**：移除輸出中的特殊 Unicode 字符，使用純 ASCII 字符
**程式碼修正**：
```python
# 避免使用 ✅ ❌ 等特殊字符
print("OK" if condition else "MISSING")
print("完成" if success else "失敗")
```

#### 問題8：GitHub 推送大檔案警告
**問題**：`townships_3826.geojson` (57.90 MB) 超過 GitHub 建議的 50MB 限制
**解決方案**：檔案已成功推送，但建議未來使用 Git LFS 處理大檔案
**建議**：
```bash
# 未來可考慮使用 Git LFS
git lfs track "*.geojson"
git add .gitattributes
```

### 學到的教訓
- 在完整整合前，先用簡單腳本測試資料來源
- 政府 API 可能會回傳需要解壓縮的 zip 檔案
- 座標系統驗證至關重要（台灣使用 EPSG:3826）
- 空間分析前資料清理是必要的 - 移除無效座標
- 資料轉換過程中要確保關鍵欄位不遺失
- 互動式地圖需要仔細檢查座標範圍和中心點
- 彈出式資訊要包含使用者需要的完整資訊
- 編碼問題要及早處理，避免影響輸出顯示

## 環境變數
```bash
BUFFER_HIGH=500    # 高風險緩衝區（公尺）
BUFFER_MED=1000    # 中風險緩衝區（公尺）
BUFFER_LOW=2000    # 低風險緩衝區（公尺）
```

## 風險等級分類
- **高風險**：避難所距離河川 500 公尺內
- **中風險**：避難所距離河川 1 公里內
- **低風險**：避難所距離河川 2 公里內
- **安全**：避難所距離河川 2 公里外

## 技術說明
- 所有空間操作在 EPSG:3826（台灣虎子窩基準1997）下執行
- 緩衝區溶解後建立統一風險區域
- 空間連接使用 'intersects' 述詞
- 風險等級指定遵循階層：高 > 中 > 低 > 安全
