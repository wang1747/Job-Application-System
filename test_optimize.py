import requests

# 先上传一份简历
upload_resp = requests.post(
    "http://127.0.0.1:8001/api/v1/resume/upload",
    json={
        "raw_text": "张三，计算机专业本科，3年Python开发经验，熟悉Django、Flask，做过电商项目",
        "source_file": "test.txt"
    }
)
resume_id = upload_resp.json()["data"]["id"]
print("简历ID:", resume_id)

# 测试优化
optimize_resp = requests.post(
    "http://127.0.0.1:8001/api/v1/resume/optimize",
    json={
        "resume_id": resume_id,
        "jd_text": "招聘Python后端工程师，要求熟悉Django、RESTful API、高并发处理，有大规模系统经验"
    }
)
print("优化结果:", optimize_resp.json())