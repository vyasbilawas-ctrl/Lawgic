import os
import re

template_dir = 'templates'
new_tag = '<a class="navbar-brand" href="/"><img src="{{ url_for(\'static\', filename=\'logo.png\') }}" alt="Lawgic" height="55" style="object-fit: contain;"></a>'

# Yeh script apne aap saari HTML files mein purane text ko nayi logo image se replace kar degi
for filename in os.listdir(template_dir):
    if filename.endswith('.html'):
        filepath = os.path.join(template_dir, filename)
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        updated_content = re.sub(r'<a[^>]*class="[^"]*navbar-brand[^"]*"[^>]*>.*?</a>', new_tag, content, flags=re.DOTALL)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(updated_content)
        print(f"✅ Logo added to {filename}")

print("Saari files successfully update ho gayi hain!")