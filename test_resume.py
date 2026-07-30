import requests

# 测试文本上传
resp = requests.post(
    "http://127.0.0.1:8001/api/v1/resume/upload",
    json={
        "raw_text": "张三，5年Python后端开发经验，熟悉Django、FastAPI，本科计算机专业",
        "source_file": "test.txt"
    }
)
print("文本上传结果:", resp.json())

# 测试列表
resp = requests.get("http://127.0.0.1:8001/api/v1/resume/list")
print("简历列表:", resp.json())