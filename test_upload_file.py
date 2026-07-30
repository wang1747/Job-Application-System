import requests

# 创建一个测试用的 txt 文件
with open('test_resume.txt', 'w', encoding='utf-8') as f:
    f.write('李四，3年Java开发经验，熟悉Spring Boot、MySQL')

# 上传文件
with open('test_resume.txt', 'rb') as f:
    files = {'file': ('test_resume.txt', f, 'text/plain')}
    resp = requests.post('http://127.0.0.1:8001/api/v1/resume/upload-file', files=files)
    print('文件上传结果:', resp.json())