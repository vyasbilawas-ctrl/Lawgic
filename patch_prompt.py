import re

with open('scraper.py', 'r', encoding='utf-8') as f:
    h = f.read()

new_prompt = '''prompt = f"""You are an expert Indian Legal Editor. Your job is to process raw RSS feed entries, especially from Indian Kanoon or other raw legal feeds, and format them perfectly.
Please follow these STRICT rules to avoid contempt of court and ensure accurate legal reporting:
1. Provide an "Ideal Heading" (TITLE): It should be professional, respectful to the courts, legally accurate, and catchy but not sensationalist.
2. Provide a "Head Note" (SUMMARY): A clear, concise, and lawful summary of the judgment/news. If the input is just a case name with no summary, infer the general nature of the case or provide a standard neutral headnote template.
3. NEVER commit contempt of court. Always use respectful language for the judiciary.

Input Data:
RAW TITLE: {title}
RAW SUMMARY: {summary}

Output exactly in this format:
TITLE: [Your Ideal Heading]
SUMMARY: [Your Head Note]
"""'''

h = re.sub(r'prompt = f\"\"\"Rewrite this.*?SUMMARY: \{summary\}\"\"\"', new_prompt, h, flags=re.DOTALL)

with open('scraper.py', 'w', encoding='utf-8') as f:
    f.write(h)
