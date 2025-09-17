import json

with open("new_data.json", "rb") as f:  # Đọc dạng bytes
    raw = f.read()

try:
    decoded = raw.decode("utf-8")
    data = json.loads(decoded)
    print("✅ JSON hợp lệ!")
except UnicodeDecodeError as e:
    print(f"❌ Lỗi Unicode: {e}")
except json.JSONDecodeError as e:
    print(f"❌ Lỗi JSON: {e}")
