import shutil
import os

# 複製避難所資料到專案目錄
source_path = r'C:\Users\admin\Desktop\遙測\data\避難收容處所(最新版).csv'
dest_dir = r'C:\Users\admin\CascadeProjects\Week3-River-Shelter-Risk\data'
dest_path = os.path.join(dest_dir, '避難收容處所.csv')

# 建立目錄
os.makedirs(dest_dir, exist_ok=True)

try:
    shutil.copy2(source_path, dest_path)
    print(f"成功複製檔案到：{dest_path}")
    print(f"檔案大小：{os.path.getsize(dest_path)} bytes")
except Exception as e:
    print(f"複製失敗：{e}")
    
# 檢查檔案是否存在
if os.path.exists(dest_path):
    print("檔案複製成功！")
else:
    print("檔案複製失敗，請檢查來源路徑")
