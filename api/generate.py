# API Vercel : génération de posts (sans Streamlit)
import json
import os
from http.server import BaseHTTPRequestHandler

SYSTEM_MESSAGE = (
    "Tu es un expert en création de contenu viral et SEO pour les réseaux sociaux. "
    "Tu crées des posts pour LinkedIn, Instagram et Facebook. "
    "RÈGLE ABSOLUE : tu dois respecter À LA LETTRE les instructions du client : "
    "nombre d'emojis (aucun / peu / beaucoup), consignes supplémentaires, ton, longueur. "
    "Ne jamais ajouter d'emojis si le client demande aucun emoji. Ne jamais ignorer une consigne explicite."
)

def _norm_tone(ton):
    t = (ton or "professionnel").lower().strip()
    if t not in ("professionnel", "humoristique", "provocateur"):
        return "professionnel"
    return t

def _emoji_rule(emoji_level):
    level = (emoji_level or "many").lower().strip()
    if level == "none" or level == "aucun" or level == "0":
        return "EMOJIS : N'utilise AUCUN emoji dans le post. Aucune exception."
    if level == "few" or level == "peu" or level == "little":
        return "EMOJIS : Utilise uniquement 3 à 5 emojis au maximum, placés avec parcimonie."
    return "EMOJIS : Utilise beaucoup d'emojis (15 à 25 selon le réseau), répartis dans tout le texte."

def get_linkedin_prompt(sujet, ton, audience, emoji_rule, custom_instructions):
    ton_fr = {"professionnel": "professionnel et sérieux", "humoristique": "humoristique et engageant", "provocateur": "provocateur et percutant"}[_norm_tone(ton)]
    base = f"""Crée un post LinkedIn professionnel LONG et DÉTAILLÉ (minimum 250-300 mots) optimisé SEO, structure AIDA.
Sujet: {sujet}
Ton: {ton_fr}
Audience cible: {audience}
STRUCTURE: accroche forte, corps détaillé (AIDA), 5-8 hashtags à la fin.
{emoji_rule}
RÉPONSE: le post complet uniquement, sans explications ni métatexte."""
    if custom_instructions:
        base += f"\n\nINSTRUCTIONS OBLIGATOIRES DU CLIENT (à respecter à la lettre):\n{custom_instructions}"
    return base

def get_instagram_prompt(sujet, ton, audience, emoji_rule, custom_instructions):
    ton_fr = {"professionnel": "professionnel", "humoristique": "décontracté et humoristique", "provocateur": "audacieux et provocateur"}[_norm_tone(ton)]
    base = f"""Crée un post Instagram LONG (minimum 200-250 mots) captivant, visuel et optimisé SEO.
Sujet: {sujet}
Ton: {ton_fr}
Audience cible: {audience}
Bloc de hashtags à la fin.
{emoji_rule}
RÉPONSE: le post complet uniquement."""
    if custom_instructions:
        base += f"\n\nINSTRUCTIONS OBLIGATOIRES DU CLIENT (à respecter à la lettre):\n{custom_instructions}"
    return base

def get_facebook_prompt(sujet, ton, audience, emoji_rule, custom_instructions):
    ton_fr = {"professionnel": "amical et professionnel", "humoristique": "décontracté et humoristique", "provocateur": "audacieux et engageant"}[_norm_tone(ton)]
    base = f"""Crée un post Facebook LONG (minimum 200-250 mots) communautaire qui encourage l'interaction.
Sujet: {sujet}
Ton: {ton_fr}
Audience cible: {audience}
Pose 3-4 questions à la fin pour encourager les commentaires.
{emoji_rule}
RÉPONSE: le post complet uniquement."""
    if custom_instructions:
        base += f"\n\nINSTRUCTIONS OBLIGATOIRES DU CLIENT (à respecter à la lettre):\n{custom_instructions}"
    return base

def build_prompt(network, subject, tone, audience, emoji_level, custom_instructions):
    prompts = {
        "linkedin": get_linkedin_prompt,
        "instagram": get_instagram_prompt,
        "facebook": get_facebook_prompt,
    }
    fn = prompts.get(network.lower(), get_linkedin_prompt)
    emoji_rule = _emoji_rule(emoji_level)
    return fn(subject or "", tone or "professionnel", audience or "", emoji_rule, (custom_instructions or "").strip())

def generate_with_mistral(prompt, api_key):
    from mistralai import Mistral
    client = Mistral(api_key=api_key)
    r = client.chat.complete(
        model="mistral-small-latest",
        messages=[
            {"role": "system", "content": SYSTEM_MESSAGE},
            {"role": "user", "content": prompt},
        ],
    )
    return r.choices[0].message.content.strip()

def generate_with_google(prompt, api_key):
    import google.generativeai as genai
    genai.configure(api_key=api_key)
    model_names = [
        "gemini-2.5-flash", "gemini-2.5-pro",
        "gemini-1.5-flash", "gemini-1.5-pro", "gemini-pro",
    ]
    for model_name in model_names:
        try:
            model = genai.GenerativeModel(model_name)
            response = model.generate_content(f"{SYSTEM_MESSAGE}\n\n{prompt}")
            return response.text.strip()
        except Exception:
            continue
    return None

def generate_post(engine, prompt, api_key_google, api_key_mistral):
    if engine == "mistral" and api_key_mistral:
        return generate_with_mistral(prompt, api_key_mistral)
    if engine == "google" and api_key_google:
        return generate_with_google(prompt, api_key_google)
    if api_key_google:
        return generate_with_google(prompt, api_key_google)
    if api_key_mistral:
        return generate_with_mistral(prompt, api_key_mistral)
    return None

def send_json(handler, status, data):
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json; charset=utf-8")
    handler.send_header("Access-Control-Allow-Origin", "*")
    handler.end_headers()
    handler.wfile.write(json.dumps(data, ensure_ascii=False).encode("utf-8"))

class handler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_POST(self):
        try:
            content_length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_length) if content_length else b"{}"
            data = json.loads(body.decode("utf-8"))
        except Exception as e:
            send_json(self, 400, {"error": "Invalid JSON", "detail": str(e)})
            return

        try:
            subject = data.get("subject", "")
            tone = data.get("tone", "professionnel")
            audience = data.get("audience", "")
            network = data.get("network", "linkedin")
            engine = data.get("engine", "google")
            emoji_level = data.get("emoji_level", "many")
            custom_instructions = data.get("custom_instructions", "")

            # Only use server-side keys (your Vercel env vars). Client never sends keys.
            api_key_google = os.environ.get("GOOGLE_AI_API_KEY")
            api_key_mistral = os.environ.get("MISTRAL_API_KEY")

            if not subject or not audience:
                send_json(self, 400, {"error": "subject et audience sont requis"})
                return

            if not api_key_google and not api_key_mistral:
                send_json(self, 503, {"error": "Service non configuré. L’administrateur doit définir GOOGLE_AI_API_KEY ou MISTRAL_API_KEY sur le serveur."})
                return

            prompt = build_prompt(network, subject, tone, audience, emoji_level, custom_instructions)
            content = generate_post(engine, prompt, api_key_google, api_key_mistral)

            if content is None:
                send_json(self, 502, {"error": "Échec de la génération (vérifiez les clés API et les quotas)."})
                return

            send_json(self, 200, {"content": content})
        except Exception as e:
            send_json(self, 500, {"error": "Erreur serveur", "detail": str(e)})
