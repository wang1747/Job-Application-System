import requests

# 需要先有一个 JD 和一个简历，使用已有的 ID
# 从之前的测试中获取
jd_id = input("请输入 JD ID: ")
resume_id = input("请输入 简历 ID: ")

resp = requests.post(
    "http://127.0.0.1:8001/api/v1/match",
    json={"jd_id": jd_id, "resume_id": resume_id}
)
print("匹配结果:", resp.json())

resp = requests.get("http://127.0.0.1:8001/api/v1/match/rankings")
print("排名列表:", resp.json())