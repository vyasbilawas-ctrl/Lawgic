import os
import json

# 1. App ki Manifest file banayenge
manifest = {
  "name": "Lawgic",
  "short_name": "Lawgic",
  "description": "Latest Legal News, Bare Acts & AI Judicial Prep",
  "start_url": "/",
  "display": "standalone",
  "background_color": "#ffffff",
  "theme_color": "#ffffff",
  "icons": [
    {
      "src": "/static/images/logo.png",
      "sizes": "192x192",
      "type": "image/png"
    },
    {
      "src": "/static/images/logo.png",
      "sizes": "512x512",
      "type": "image/png"
    }
  ]
}

if not os.path.exists('static'):
    os.makedirs('static')
    
with open('static/manifest.json', 'w', encoding='utf-8') as f:
    json.dump(manifest, f, indent=4)
print("✅ manifest.json file ban gayi.")

# 2. Service Worker add karenge
sw_code = """
self.addEventListener('install', (e) => {
  console.log('[PWA] Service Worker Installed');
});
self.addEventListener('fetch', (e) => {
  // Pass-through for PWA installability
});
"""
with open('static/sw.js', 'w', encoding='utf-8') as f:
    f.write(sw_code)
print("✅ Service Worker (sw.js) file ban gayi.")

# 3. app.py mein sw.js ka route add karenge
with open("app.py", "r", encoding="utf-8") as f:
    app_code = f.read()

route_code = """
@app.route('/sw.js')
def serve_sw():
    from flask import send_from_directory
    return send_from_directory('static', 'sw.js')
"""
if 'serve_sw' not in app_code:
    app_code = app_code.replace('if __name__ == "__main__":', route_code + '\nif __name__ == "__main__":')
    with open("app.py", "w", encoding="utf-8") as f:
        f.write(app_code)
    print("✅ app.py mein route add ho gaya.")

# 4. HTML files mein App ke Meta tags aur script lagayenge
pwa_tags = """
    <!-- PWA Settings -->
    <link rel="manifest" href="/static/manifest.json">
    <meta name="theme-color" content="#ffffff">
    <meta name="apple-mobile-web-app-capable" content="yes">
    <meta name="apple-mobile-web-app-status-bar-style" content="black">
    <script>
      if ('serviceWorker' in navigator) {
        window.addEventListener('load', () => {
          navigator.serviceWorker.register('/sw.js');
        });
      }
    </script>
"""

for filename in os.listdir('templates'):
    if filename.endswith('.html'):
        with open(os.path.join('templates', filename), 'r', encoding='utf-8') as f:
            content = f.read()
        
        if 'rel="manifest"' not in content:
            if '</head>' in content:
                content = content.replace('</head>', pwa_tags + '\n</head>')
            
            with open(os.path.join('templates', filename), 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"✅ App tags {filename} mein add ho gaye")

print("🎉 PWA setup poora ho gaya!")