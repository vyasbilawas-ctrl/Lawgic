import urllib.request
import time

url = "https://verdicthub-live.onrender.com/"
print("Checking for Judicial Prep link in navbar...")
for i in range(12):
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            content = resp.read().decode('utf-8')
            if 'href="/judicial-exam"' in content:
                print("SUCCESS: Judicial Prep link found on live homepage!")
                break
            else:
                print(f"[{i+1}/12] Still deploying previous build... waiting 10s")
    except Exception as e:
        print(f"[{i+1}/12] Server restarting... waiting 10s ({e})")
    time.sleep(10)
