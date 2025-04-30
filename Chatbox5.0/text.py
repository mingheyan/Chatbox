import requests
cookies={
    'csrftoken': 'HM6PQhUEOAIYkeeNLlhl2YNMgUAGDxpP',
    'sessionid': 'k7o903bx0b3f9myfvq3gbk68i76ew35l',
}
r = requests.post('http://127.0.0.1:8000/api/generate_secret_key/', cookies=cookies)
print(r.json())