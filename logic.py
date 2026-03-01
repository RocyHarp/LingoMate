import google.generativeai as genai
import json
import warnings
from deep_translator import GoogleTranslator
import requests
import random
import pytesseract
from PIL import Image
import os

warnings.filterwarnings("ignore")

class backendLogic:
    def __init__(self):
        self.api_keys = ["AIzaSyAdTf9QDtWG-NRqCZEdiRwJUJhD5RhDOCI"] 
        self.safety_config = [
            {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
        ]
        self.working_models = ['gemini-2.0-flash', 'gemini-1.5-flash']

    def _clean_json_text(self, text):
        try:
            text = text.replace("```json", "").replace("```", "").strip()
            start = text.find("{")
            end = text.rfind("}")
            if start != -1 and end != -1:
                return text[start:end+1]
            return text
        except: return "{}"

    def analyze_with_ai(self, text, direction="EN-UA", use_ai=True):
        if not use_ai:
            try:
                if "UA" in direction and "EN" not in direction[:2]: src, trg = 'uk', 'en'
                else: src, trg = 'en', 'uk'
                trans = GoogleTranslator(source=src, target=trg).translate(text)
                return {"translation": trans, "context_ua": "", "vocabulary": []}
            except Exception as e: return {"translation": "Error", "context_ua": str(e), "vocabulary": []}

        print(f"🚀 AI Аналіз...")
        for key in self.api_keys:
            genai.configure(api_key=key)
            for model_name in self.working_models:
                try:
                    model = genai.GenerativeModel(model_name)
                    prompt = f"""
                    Act as an English/Ukrainian translator.
                    Task 1: Translate: "{text}" (Direction: {direction}).
                    Task 2: Explain grammar/context briefly in 'context_ua'.
                    Task 3: IF input is a sentence, extract key words/phrases to 'vocabulary'.
                    Response MUST be strict JSON.
                    """
                    response = model.generate_content(prompt, safety_settings=self.safety_config, request_options={'timeout': 15})
                    if not response.parts: continue
                    return json.loads(self._clean_json_text(response.text))
                except Exception as e:
                    print(f"Translate Error {model_name}: {e}")
                    continue
        try:
            trans = GoogleTranslator(source='auto', target='uk').translate(text)
            return {"translation": trans, "context_ua": "⚠️ AI Error / 404 (Перевір ключ або з'єднання)", "vocabulary": []}
        except Exception as e: return {"translation": "Error", "context_ua": str(e), "vocabulary": []}

    def explain_nuance(self, word, context_sentence="", meaning=""):
        print(f"💡 Пояснюю нюанс: {word}")
        context_info = f"Meaning: '{meaning}'" if not context_sentence and meaning else f"Context: '{context_sentence}'"
        for key in self.api_keys:
            genai.configure(api_key=key)
            for model_name in self.working_models:
                try:
                    model = genai.GenerativeModel(model_name)
                    prompt = f"""Word: "{word}"\n{context_info}\nTask: Explain NUANCE in Ukrainian.\nJSON ONLY: {{ "synonym_en": "...", "synonym_ua": "...", "explanation": "..." }}"""
                    response = model.generate_content(prompt, safety_settings=self.safety_config, request_options={'timeout': 8})
                    if not response.candidates: return {"synonym_en": "N/A", "synonym_ua": "Блок", "explanation": "Google AI заблокував."}
                    return json.loads(self._clean_json_text(response.text))
                except Exception as e: continue
        return {"synonym_en": "Error", "synonym_ua": "Помилка", "explanation": "Не вдалося підключитися до AI."}

    def get_text_from_image(self, image_path):
        try:
            # Розумна перевірка: якщо ми на твоєму Mac, використовуємо твій шлях
            if os.path.exists('/opt/homebrew/bin/tesseract'):
                pytesseract.pytesseract.tesseract_cmd = '/opt/homebrew/bin/tesseract'
                
            text = pytesseract.image_to_string(Image.open(image_path), lang='eng+ukr').strip()
            return text
        except Exception as e:
            # Якщо щось піде не так, ми побачимо текст помилки замість мовчання
            return f"Помилка сканера: {str(e)}"
        
    def fetch_and_translate_words(self, count, use_ai=True):
        if use_ai:
            print(f"🧠 AI генерує слова...")
            for key in self.api_keys:
                genai.configure(api_key=key)
                for model_name in self.working_models:
                    try:
                        model = genai.GenerativeModel(model_name)
                        prompt = f"Generate {count} USEFUL English words (B1-C1). JSON List. Format: [{{'word': '...', 'meaning': '...', 'type': 'noun/verb/etc'}}]"
                        response = model.generate_content(prompt, request_options={'timeout': 20})
                        return json.loads(self._clean_json_text(response.text))
                    except Exception as e: continue
            print("⚠️ AI Failed.")

        print("🎲 Старий метод...")
        added = []
        try:
            all_words = requests.get("https://raw.githubusercontent.com/first20hours/google-10000-english/master/google-10000-english-usa-no-swears-medium.txt").text.splitlines()
            chosen = random.sample(all_words[:3000], count + 5)
            translator = GoogleTranslator(source='en', target='uk')
            for w in chosen:
                if len(added) >= count: break
                if len(w) > 3:
                    try: added.append({"word": w, "meaning": translator.translate(w), "type": "auto"})
                    except: continue
            return added
        except: return []

    def find_synonyms(self, word, user_context_ua=""):
        print(f"🔍 Шукаю синоніми до '{word}'...")
        result_list, seen_words = [], set()
        translator = GoogleTranslator(source='en', target='uk')
        context_en = ""
        try:
            if user_context_ua: context_en = GoogleTranslator(source='uk', target='en').translate(user_context_ua)
        except: pass
        if context_en and context_en.lower() != word.lower():
            try:
                result_list.append({"word": context_en.lower(), "translation": user_context_ua, "nuance": "Пряме значення"})
                seen_words.add(context_en.lower())
            except: pass
        def fetch_datamuse(url, nuance_desc):
            try:
                resp = requests.get(url, timeout=4).json()
                for item in resp:
                    if len(result_list) >= 3: return
                    syn = item['word'].lower()
                    if syn == word.lower() or syn in seen_words: continue
                    try:
                        tr = translator.translate(syn)
                        if tr.lower() == syn: continue
                        result_list.append({"word": syn, "translation": tr, "nuance": nuance_desc})
                        seen_words.add(syn)
                    except: continue
            except: pass
        if context_en:
            fetch_datamuse(f"https://api.datamuse.com/words?rel_syn={word}&topics={context_en}", "Контекстний синонім")
            if len(result_list) < 3: fetch_datamuse(f"https://api.datamuse.com/words?ml={word}&topics={context_en}", "Схоже за значенням")
        if len(result_list) < 3: fetch_datamuse(f"https://api.datamuse.com/words?rel_syn={word}", "Синонім")
        return result_list
