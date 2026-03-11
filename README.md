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
- **收容量缺口分析**：識別安全避難所收容量不足的行政區
- **互動式視覺化**：使用 Folium 製作依風險等級著色的地圖
- **自動化報告**：匯出避難所風險評估 JSON 檔案

## 交付成果
- `ARIA.ipynb` - 完整分析筆記本
- `shelter_risk_audit.json` - 避難所風險分類
- `risk_map.html` - 互動式風險地圖
- `risk_chart.png` - 高風險區域前10名圖表

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

### 學到的教訓
- 在完整整合前，先用簡單腳本測試資料來源
- 政府 API 可能會回傳需要解壓縮的 zip 檔案
- 座標系統驗證至關重要（台灣使用 EPSG:3826）
- 空間分析前資料清理是必要的 - 移除無效座標

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
