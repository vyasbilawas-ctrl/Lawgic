import re

with open('scraper.py', 'r', encoding='utf-8') as f:
    code = f.read()

# Make sure 're' module is imported
if 'import re' not in code:
    code = "import re\n" + code

# Yeh powerful filter database mein save hone se theek pehle kisi bhi URL ko Title se kaat dega
hook = """
        # Automatically clean URLs from title before saving
        for var_name in ['article', 'new_article', 'item']:
            obj = locals().get(var_name)
            if obj and hasattr(obj, 'title') and obj.title:
                # Remove http:// or https:// or www.
                obj.title = re.sub(r'(?i)https?://\S+|www\.\S+', '', str(obj.title)).strip()
                # Remove any trailing colons or hyphens left behind (e.g. "News Title : " -> "News Title")
                obj.title = re.sub(r'[-:\|]+$', '', obj.title).strip()
        
        session.add("""
        
if "# Automatically clean URLs" not in code:
    code = code.replace("session.add(", hook)
    with open('scraper.py', 'w', encoding='utf-8') as f:
        f.write(code)
    print("✅ Scraper updated! Ab titles ekdum clean aayenge.")
else:
    print("Filter pehle se laga hua hai.")