with open('templates/index.html', 'r', encoding='utf-8') as f:
    h = f.read()
h = h.replace('<a class="nav-link" href="/ai-search"><i class="fas fa-robot"></i>AI Research</a>', '')
h = h.replace('<li><a href="/ai-search"><i class="fas fa-robot"></i> AI Search</a></li>', '')
h = h.replace('<li><a href="/ai-search">AI Research</a></li>', '')
with open('templates/index.html', 'w', encoding='utf-8') as f:
    f.write(h)
