import requests

resp = requests.post(
    "http://127.0.0.1:8001/api/v1/jd/parse",
    json={"raw_text": "职位：Python后端开发工程师，公司：字节跳动，要求：本科以上，3年以上Python经验，熟悉Django"}
)
print(resp.json())
