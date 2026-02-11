import json
import os

def get_i10n_text(language, text):
    path = f"i10n/{language}.json"
    if not os.path.exists(path):
        return f"[Missing i10n file: {language}]"
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data.get(text, f"[Missing key: {text}]")
    except Exception as e:
        return f"[i10n Error: {e}]"