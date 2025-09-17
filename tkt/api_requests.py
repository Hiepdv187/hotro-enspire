import requests
api_key = 'access_token'
api_url = "https://account.base.vn/extapi/v1/users"
data = {'access_token': '7868-GTFZBC5SQV3VTQBQK7NFPYUAB79X9Y7AX7PJUM47NT6Y3FJ2WHUBHM9KBNV59RPB-RUSA9JWQLXMULB9UPF3LV564BUEHHR7UD93HDGNYB25XVDLP5VKEL2X44XYR68PJ'}

response = requests.post(api_url, data=data)

# Check if request was successful
if response.status_code == 200:
    print(response.json())
else:
    print(f"Request failed with status code {response.status_code}")
    api_users = []


