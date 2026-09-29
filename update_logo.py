import glob
import re

for f in glob.glob('templates/*.html'):
    with open(f, 'r', encoding='utf-8') as file:
        content = file.read()
    
    # Replace old image logo with awesome CSS logo
    new_logo = '<i class="fas fa-balance-scale-right me-2" style="color: var(--accent-color); font-size: 1.6rem;"></i><span style="color: var(--primary-color);">Law</span><span style="color: var(--accent-color);">gic</span>'
    content = re.sub(r'<img src="/static/images/logo\.jpg" alt="Logo">\s*VerdictHub', new_logo, content)
    content = content.replace('VerdictHub', 'Lawgic').replace('verdicthub', 'lawgic')
    
    with open(f, 'w', encoding='utf-8') as file:
        file.write(content)
