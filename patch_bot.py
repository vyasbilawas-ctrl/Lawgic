import re

with open('templates/index.html', 'r', encoding='utf-8') as f:
    html = f.read()

bot_html = """
    <!-- Floating AI Bot -->
    <div id="ai-bot-container" style="position: fixed; bottom: 20px; right: 20px; z-index: 1000; font-family: 'Inter', sans-serif;">
        <div id="ai-bot-window" style="display: none; width: 350px; height: 500px; background: white; border-radius: 12px; box-shadow: 0 10px 30px rgba(0,0,0,0.15); border: 1px solid var(--line); flex-direction: column; overflow: hidden; margin-bottom: 15px;">
            <div style="background: var(--primary); color: white; padding: 15px; font-family: 'Cinzel', serif; display: flex; justify-content: space-between; align-items: center;">
                <h5 style="margin: 0; font-weight: 700;"><i class="fas fa-robot" style="color: var(--accent); margin-right: 8px;"></i> Lawgic AI Assistant</h5>
                <button onclick="toggleBot()" style="background: none; border: none; color: white; cursor: pointer;"><i class="fas fa-times"></i></button>
            </div>
            <div id="ai-bot-messages" style="flex: 1; padding: 15px; overflow-y: auto; display: flex; flex-direction: column; gap: 10px; background: #f9fafb;">
                <div style="align-self: flex-start; background: #e7eaf0; padding: 10px 14px; border-radius: 12px; max-width: 85%; font-size: 0.9rem; color: var(--text);">
                    Hello! I'm your Indian Legal AI Assistant. Ask me any legal question.
                </div>
            </div>
            <div style="padding: 15px; border-top: 1px solid var(--line); background: white;">
                <form id="ai-bot-form" style="display: flex; gap: 10px;">
                    <input type="text" id="ai-bot-input" placeholder="Ask a legal question..." style="flex: 1; padding: 10px; border: 1px solid #ddd; border-radius: 8px; outline: none; font-size: 0.9rem;" required>
                    <button type="submit" style="background: var(--primary); color: white; border: none; padding: 0 15px; border-radius: 8px; cursor: pointer;"><i class="fas fa-paper-plane"></i></button>
                </form>
            </div>
        </div>
        <button id="ai-bot-toggle" onclick="toggleBot()" style="float: right; width: 60px; height: 60px; border-radius: 50%; background: var(--primary); color: white; border: none; box-shadow: 0 5px 15px rgba(0,0,0,0.2); font-size: 1.5rem; cursor: pointer; display: flex; justify-content: center; align-items: center; transition: transform 0.2s;">
            <i class="fas fa-robot"></i>
        </button>
    </div>

    <script>
    function toggleBot() {
        const win = document.getElementById('ai-bot-window');
        win.style.display = win.style.display === 'none' ? 'flex' : 'none';
        if(win.style.display === 'flex') document.getElementById('ai-bot-input').focus();
    }

    document.getElementById('ai-bot-form').onsubmit = function(e) {
        e.preventDefault();
        const input = document.getElementById('ai-bot-input');
        const query = input.value.trim();
        if(!query) return;
        
        const msgs = document.getElementById('ai-bot-messages');
        
        // Add User message
        const userDiv = document.createElement('div');
        userDiv.style = "align-self: flex-end; background: var(--primary); color: white; padding: 10px 14px; border-radius: 12px; max-width: 85%; font-size: 0.9rem;";
        userDiv.innerText = query;
        msgs.appendChild(userDiv);
        input.value = '';
        
        // Add Loading message
        const loadDiv = document.createElement('div');
        loadDiv.style = "align-self: flex-start; background: #e7eaf0; padding: 10px 14px; border-radius: 12px; max-width: 85%; font-size: 0.9rem; color: var(--muted);";
        loadDiv.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Thinking...';
        msgs.appendChild(loadDiv);
        msgs.scrollTop = msgs.scrollHeight;

        fetch('/api/ask-ai', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({query: query})
        })
        .then(r => r.json())
        .then(data => {
            msgs.removeChild(loadDiv);
            const aiDiv = document.createElement('div');
            aiDiv.style = "align-self: flex-start; background: white; border: 1px solid var(--line); padding: 10px 14px; border-radius: 12px; max-width: 90%; font-size: 0.9rem; color: var(--text); line-height: 1.5;";
            aiDiv.innerHTML = data.response || data.error;
            msgs.appendChild(aiDiv);
            msgs.scrollTop = msgs.scrollHeight;
        })
        .catch(err => {
            msgs.removeChild(loadDiv);
            const errDiv = document.createElement('div');
            errDiv.style = "align-self: flex-start; background: #ffebee; color: #c62828; padding: 10px 14px; border-radius: 12px; max-width: 85%; font-size: 0.9rem;";
            errDiv.innerText = 'Unable to reach AI server.';
            msgs.appendChild(errDiv);
            msgs.scrollTop = msgs.scrollHeight;
        });
    };
    </script>
"""

if '<!-- Floating AI Bot -->' not in html:
    html = html.replace('</body>', bot_html + '\n</body>')
    with open('templates/index.html', 'w', encoding='utf-8') as f:
        f.write(html)
