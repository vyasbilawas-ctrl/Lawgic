import os
import re

template_dir = 'templates'

for filename in os.listdir(template_dir):
    if filename.endswith('.html'):
        filepath = os.path.join(template_dir, filename)
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Yeh code check karega: Agar image fail hoti hai, toh uski jagah Lawgic ka logo laga dega
        updated = re.sub(
            r'(<img[^>]*?src=["\']\{\{.*?\}\}["\'][^>]*?)(/?>)',
            r'\1 onerror="this.onerror=null; this.src=\'/static/images/logo.png\';"\2',
            content
        )
        
        # Double check (taaki galti se 2 baar add na ho)
        updated = updated.replace('onerror="this.onerror=null; this.src=\'/static/images/logo.png\';" onerror', 'onerror')

        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(updated)
        print(f"✅ Fixed broken images in {filename}")

print("🎉 Ab broken images ki jagah logo dikhega!")