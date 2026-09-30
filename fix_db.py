with open('app.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 'init_db' ko imports aur code se hata rahe hain
content = content.replace('from database import init_db,', 'from database import')
content = content.replace('init_db()\n', '')

with open('app.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("✅ app.py se init_db successfully hata diya gaya hai!")