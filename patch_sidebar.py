import re

with open('templates/index.html', 'r', encoding='utf-8') as f:
    html = f.read()

# Make sidebar sticky
sidebar_css = '''        .sidebar {
            display: flex;
            flex-direction: column;
            gap: 22px;
            position: sticky;
            top: 100px;
            align-self: start;
        }'''
html = re.sub(r'\.sidebar\s*\{\s*display:\s*flex;\s*flex-direction:\s*column;\s*gap:\s*22px;\s*\}', sidebar_css, html)

# Add a widget to the sidebar
new_widget = '''
            <div class="side-card" style="background: linear-gradient(135deg, var(--primary), var(--primary-2)); color: white; text-align: center;">
                <i class="fas fa-gavel" style="font-size: 2.5rem; color: var(--accent); margin-bottom: 15px;"></i>
                <h4 style="color: white; font-family: 'Playfair Display', serif;">Deep Legal Research</h4>
                <p style="font-size: 0.9rem; opacity: 0.9; margin-bottom: 20px;">Use our AI to analyze judgments, drafts, and get instant answers based on Indian Law.</p>
                <a href="/ai-search" class="btn" style="background: var(--accent); color: var(--primary); font-weight: 700; width: 100%; border-radius: 8px; padding: 10px;">Try AI Search</a>
            </div>
            
            <div class="side-card">
                <h4>Top Categories</h4>
                <div style="display: flex; flex-wrap: wrap; gap: 8px; margin-top: 15px;">
                    <a href="/?category=Supreme+Court" style="padding: 6px 12px; background: var(--bg); border: 1px solid var(--line); border-radius: 20px; font-size: 0.85rem; color: var(--text); text-decoration: none;">Supreme Court</a>
                    <a href="/?category=High+Court" style="padding: 6px 12px; background: var(--bg); border: 1px solid var(--line); border-radius: 20px; font-size: 0.85rem; color: var(--text); text-decoration: none;">High Court</a>
                    <a href="/?category=Criminal+Law" style="padding: 6px 12px; background: var(--bg); border: 1px solid var(--line); border-radius: 20px; font-size: 0.85rem; color: var(--text); text-decoration: none;">Criminal Law</a>
                    <a href="/?category=Corporate+Law" style="padding: 6px 12px; background: var(--bg); border: 1px solid var(--line); border-radius: 20px; font-size: 0.85rem; color: var(--text); text-decoration: none;">Corporate Law</a>
                </div>
            </div>
'''

html = html.replace('<div class="side-card newsletter">', new_widget + '\n<div class="side-card newsletter">')

with open('templates/index.html', 'w', encoding='utf-8') as f:
    f.write(html)
