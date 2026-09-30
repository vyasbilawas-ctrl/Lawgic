import os
import re

# 1. app.py mein safe filter add karenge
with open('app.py', 'r', encoding='utf-8') as f:
    app_code = f.read()

filter_code = """
import re
def jinja_clean_title(text):
    if not text: return ""
    # Sabhi tarah ke URLs (http, https, www) ko hata dega
    t = re.sub(r'(?i)https?://\S+|www\.\S+', '', str(text)).strip()
    # Aakhiri bache hue extra symbols (jaise : ya -) ko bhi hatae
    return re.sub(r'[-:\|]+$', '', t).strip()
app.jinja_env.filters['clean_title'] = jinja_clean_title
"""

if "jinja_clean_title" not in app_code:
    app_code = app_code.replace('if __name__ == "__main__":', filter_code + '\nif __name__ == "__main__":')
    with open('app.py', 'w', encoding='utf-8') as f:
        f.write(app_code)
    print("✅ Filter logic added to app.py")

# 2. Saari HTML files mein us filter ko automatically laga denge
for filename in os.listdir('templates'):
    if filename.endswith('.html'):
        filepath = os.path.join('templates', filename)
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        if "| clean_title" not in content:
            updated_content = re.sub(r'\b([a-zA-Z0-9_]+)\.title\s*\}\}', r'\1.title | clean_title }}', content)
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(updated_content)
            print(f"✅ Clean titles filter applied to {filename}")

print("🎉 Perfect! Frontend titles ab humesha clean rahenge.")