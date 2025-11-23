import requests

url = "https://www.nvcc.edu/academics/schedule/crs2262/search"
params = {
    "subject": "ITN",
    "page": 2
}
headers = {
    "User-Agent": "Mozilla/5.0",
    "X-Requested-With": "XMLHttpRequest"
}

try:
    response = requests.get(url, params=params, headers=headers)
    print(f"Status Code: {response.status_code}")
    print(f"URL: {response.url}")
    print(f"Content snippet: {response.text[:500]}")
    if "ITN 100" in response.text:
        print("Found ITN 100 (Page 1 content?)")
    else:
        print("ITN 100 not found (Maybe Page 2?)")
except Exception as e:
    print(f"Error: {e}")
