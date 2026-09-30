import os

app_id = "d92d6bef-4c5b-4099-8c2b-1bdf5819383f"

# 1. Create OneSignal Worker
if not os.path.exists('static'):
    os.makedirs('static')
with open('static/OneSignalSDKWorker.js', 'w', encoding='utf-8') as f:
    f.write("importScripts('https://cdn.onesignal.com/sdks/web/v16/OneSignalSDKWorker.js');")
print("✅ Worker file created in static folder.")

# 2. Add route in app.py
with open("app.py", "r", encoding="utf-8") as f:
    app_code = f.read()

route_code = """
@app.route('/OneSignalSDKWorker.js')
def serve_onesignal_worker():
    from flask import send_from_directory
    return send_from_directory('static', 'OneSignalSDKWorker.js')
"""
if 'serve_onesignal_worker' not in app_code:
    app_code = app_code.replace('if __name__ == "__main__":', route_code + '\nif __name__ == "__main__":')
    with open("app.py", "w", encoding="utf-8") as f:
        f.write(app_code)
    print("✅ Route added to app.py.")

# 3. Add script to HTML templates
script_code = f"""
    <!-- OneSignal Push Notifications -->
    <script src="https://cdn.onesignal.com/sdks/web/v16/OneSignalSDK.page.js" defer></script>
    <script>
      window.OneSignalDeferred = window.OneSignalDeferred || [];
      OneSignalDeferred.push(function(OneSignal) {{
        OneSignal.init({{
          appId: "{app_id}",
        }});
      }});
    </script>
"""

for filename in os.listdir('templates'):
    if filename.endswith('.html'):
        with open(os.path.join('templates', filename), 'r', encoding='utf-8') as f:
            content = f.read()
        
        if 'OneSignalSDK.page.js' not in content:
            if '</head>' in content:
                content = content.replace('</head>', script_code + '\n</head>')
            else:
                content = script_code + '\n' + content
            
            with open(os.path.join('templates', filename), 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"✅ Notification script added to {filename}")

print("🎉 Push Notifications successfully setup ho gaye!")