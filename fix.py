import re

with open('templates/index.html', 'r', encoding='utf-8') as f:
    html = f.read()

html = html.replace('info@lawgic.com', 'inikhilvyas@gmail.com')
html = html.replace('+91-XXXXXXXXXX', '+91-9414121172')

html = html.replace('<div class="ms-auto d-flex align-items-center flex-wrap">', 
'<div class="ms-auto d-flex align-items-center flex-wrap"><div id="google_translate_element" style="margin-right: 15px;"></div>')

html = html.replace('</body>', '''
<script type="text/javascript">
function googleTranslateElementInit() {
  new google.translate.TranslateElement({pageLanguage: 'en', includedLanguages: 'hi,en', layout: google.translate.TranslateElement.InlineLayout.SIMPLE}, 'google_translate_element');
}
</script>
<script type="text/javascript" src="//translate.google.com/translate_a/element.js?cb=googleTranslateElementInit"></script>
</body>''')

html = re.sub(
    r'<div class="featured-image">\s*<i class="fas fa-gavel"></i>\s*</div>',
    '''<div class="featured-image">
                  {% if articles[0].image_url %}
                      <img src="{{ articles[0].image_url }}" alt="Featured Image" style="width: 100%; height: 100%; object-fit: cover;">
                  {% else %}
                      <i class="fas fa-gavel"></i>
                  {% endif %}
              </div>''',
    html, flags=re.DOTALL
)

html = re.sub(
    r'<div class="article-thumb">\s*<i class="fas fa-file-contract"></i>\s*</div>',
    '''<div class="article-thumb">
                          {% if article.image_url %}
                              <img src="{{ article.image_url }}" alt="News Image" style="width: 100%; height: 100%; object-fit: cover;">
                          {% else %}
                              <i class="fas fa-file-contract"></i>
                          {% endif %}
                      </div>''',
    html, flags=re.DOTALL
)

with open('templates/index.html', 'w', encoding='utf-8') as f:
    f.write(html)
