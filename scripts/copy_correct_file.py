import shutil
import os

# 正確的檔案名稱（從Get-ChildItem輸出）
source_filename = '避難收容處所最新版9.csv'
source_path = fr'C:\Users\admin\Desktop\遙測\data\{source_filename}'
dest_path = r'C:\Users\admin\CascadeProjects\Week3-River-Shelter-Risk\data\避難收容處所點位檔案v9.csv'

# 建立目錄
os.makedirs(os.path.dirname(dest_path), exist_ok=True)

print(f"嘗試複製：{source_path}")
print(f"目標路徑：{dest_path}")

# 先列出所有可能的檔案
print("檢查可能的檔案名稱：")
data_dir = r'C:\Users\admin\Desktop\遙測\data'
if os.path.exists(data_dir):
    for file in os.listdir(data_dir):
        if '避難' in file and file.endswith('.csv'):
            print(f"找到：{file}")
            source_path = os.path.join(data_dir, file)
            if os.path.exists(source_path):
                try:
                    shutil.copy2(source_path, dest_path)
                    print(f"成功複製：{file}")
                    print(f"檔案大小：{os.path.getsize(dest_path)} bytes")
                    break
                except Exception as e:
                    print(f"複製失敗：{e}")
else:
    print("目錄不存在")
