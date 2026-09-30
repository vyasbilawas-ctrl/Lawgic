import os
import re

for filename in os.listdir('templates'):
    if filename.endswith('.html'):
        filepath = os.path.join('templates', filename)
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Function jo broken link ko logo se replace karega SERVER par hi
        def replacer(match):
            var_name = match.group(1).strip()
            if 'url_for' in var_name or ' else ' in var_name:
                return match.group(0) # Agar pehle se theek hai toh chhod do
            
            return f'src="{{{{ {var_name} if {var_name} and {var_name} != \'None\' else url_for(\'static\', filename=\'images/logo.png\') }}}}"'
        
        # image_url dhoondh kar jinja logic lagana
        updated = re.sub(r'src=["\']\{\{\s*(.*?image_url.*?)\s*\}\}["\']', replacer, content)
        
        # Purana fail hone wala JavaScript (onerror) hata dena
        updated = re.sub(r'\s*onerror=["\'].*?["\']', '', updated)

        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(updated)
        print(f"✅ Image rendering perfectly fixed in {filename}")

print("🎉 Master Fix Successfully Applied!")