import urllib.request
import re
html = urllib.request.urlopen('https://lawgic-live.onrender.com/').read().decode('utf-8')
urls = re.findall(r'<img src="([^"]+)"', html)
for u in urls:
    print(u)
