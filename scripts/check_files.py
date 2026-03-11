import os

# 檢查遙測目錄下的所有檔案
remote_dir = r'C:\Users\admin\Desktop\遙測\data'

print("檢查遙測資料目錄內容：")
if os.path.exists(remote_dir):
    for file in os.listdir(remote_dir):
        if file.endswith('.csv'):
            file_path = os.path.join(remote_dir, file)
            print(f"找到CSV檔案：{file}")
            print(f"完整路徑：{file_path}")
            print(f"檔案大小：{os.path.getsize(file_path)} bytes")
            print("---")
else:
    print("目錄不存在")

# 檢查可能的檔案名稱
possible_names = [
    '避難收容處所.csv',
    '避難收容處所(最新版).csv',
    'shelters.csv',
    'emergency_shelters.csv'
]

print("\n檢查可能的檔案名稱：")
for name in possible_names:
    test_path = os.path.join(remote_dir, name)
    if os.path.exists(test_path):
        print(f"找到：{test_path}")
    else:
        print(f"不存在：{test_path}")
