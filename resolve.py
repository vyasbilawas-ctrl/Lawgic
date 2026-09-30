import re

with open('app.py', 'r', encoding='utf-8') as f:
    code = f.read()

resolved = re.sub(r'<<<<<<< HEAD.*?=======.*?(?=        return jsonify\({"response": answer}\))', '''        import markdown

        genai.configure(api_key=api_key)
        model = genai.GenerativeModel(os.getenv("GEMINI_MODEL", "gemini-2.5-pro"))
        prompt = f"""You are Lawgic's careful Indian legal research assistant. Answer in {language}.
Answer this question: {query}

Give a clear, neutral answer based on Indian law. Use markdown for formatting (e.g. **bold**, lists).
Explain that this is general information, not legal advice. Do not invent citations. If uncertain, say so.
At the end, list 2-4 relevant real judgments only when you are confident they are relevant, with the case name and one-sentence holding."""
        response = model.generate_content(prompt, request_options={"timeout": 120})
        answer = getattr(response, "text", "").strip()
        if not answer:
            raise ValueError("The AI returned an empty response")
            
        html_answer = markdown.markdown(answer)
        answer = bleach.clean(
            html_answer,
            tags=["p", "br", "strong", "ul", "ol", "li", "em", "b", "i", "h1", "h2", "h3", "h4", "h5", "h6"],
            attributes={},
            strip=True,
        )
''', code, flags=re.DOTALL)

resolved = re.sub(r'>>>>>>> d0a9173.*?\n', '', resolved)

with open('app.py', 'w', encoding='utf-8') as f:
    f.write(resolved)
