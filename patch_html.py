import re

with open('templates/index.html', 'r', encoding='utf-8') as f:
    html = f.read()

# Update newsletter frontend
newsletter_html = '''
            <div class="side-card newsletter">
                <h4>Newsletter</h4>
                <p>Get daily legal updates in your inbox.</p>
                <div id="newsletter-message" style="display:none; color: green; font-size: 0.9rem; margin-bottom: 10px;"></div>
                <input type="email" id="newsletter-email" placeholder="Enter your email">
                <button type="button" onclick="subscribe()">Subscribe</button>
            </div>
            
            <script>
            function subscribe() {
                const email = document.getElementById('newsletter-email').value;
                const msg = document.getElementById('newsletter-message');
                msg.style.display = 'block';
                msg.style.color = '#333';
                msg.innerText = 'Subscribing...';
                
                fetch('/api/subscribe', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({email: email})
                })
                .then(r => r.json())
                .then(data => {
                    msg.innerText = data.message || data.error;
                    msg.style.color = data.error ? 'red' : 'green';
                    if(!data.error) document.getElementById('newsletter-email').value = '';
                })
                .catch(err => {
                    msg.innerText = 'An error occurred.';
                    msg.style.color = 'red';
                });
            }
            </script>
'''

html = re.sub(
    r'<div class="side-card newsletter">.*?<button type="button">Subscribe</button>\s*</div>',
    newsletter_html,
    html,
    flags=re.DOTALL
)

with open('templates/index.html', 'w', encoding='utf-8') as f:
    f.write(html)
