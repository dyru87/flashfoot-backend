from flask import Flask, jsonify
from flask_cors import CORS
import os
import openai
import feedparser
from datetime import datetime
import threading
import time
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
CORS(app)

openai.api_key = os.getenv("OPENAI_API_KEY")

RSS_FEEDS = [
    "https://www.topmercato.com/feed/",
    "https://www.footmercato.net/rss",
    "https://www.football.fr/feed/rss",
    "https://www.dailymercato.com/rss",
    "https://www.butfootballclub.fr/rss"
]

CATEGORIES = {
    "Ligue 1": ["PSG", "OM", "OL", "Monaco", "Lens", "Rennes", "Toulouse"],
    "Liga": ["Barcelone", "Real Madrid", "Atletico", "Seville"],
    "Serie A": ["Juventus", "Milan", "Naples", "Inter"],
    "Premier League": ["Manchester", "Arsenal", "Chelsea", "Liverpool", "Tottenham"],
    "Monde": []
}

breves_stock = []

@app.route("/api/breves")
def get_breves():
    return jsonify(breves_stock)

def fetch_and_generate_breves():
    print("🛠️ Génération automatique des brèves")
    try:
        breves_stock.clear()
        articles = []

        for url in RSS_FEEDS:
            feed = feedparser.parse(url)
            for entry in feed.entries:
                articles.append({"title": entry.title, "content": entry.get("summary", "")})

        articles = articles[:30]

        for art in articles:
            titre = art["title"]
            contenu = art["content"]

            prompt = f"""
Résume cet article en 400 caractères max dans un style journalistique, sans mention du site ou de lien, en mettant en valeur l'info :\n\nTitre : {titre}\nContenu : {contenu}\n
Format de réponse :\n{{\n  \"title\": \"...\",\n  \"content\": \"...\"\n}}
"""
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7
            )

            texte = response.choices[0].message.content.strip()
            if texte.startswith("{"):
                cat = "Monde"
                for nom, mots in CATEGORIES.items():
                    if any(mot.lower() in titre.lower() for mot in mots):
                        cat = nom
                        break

                breve = eval(texte)
                breve["category"] = cat
                breve["date"] = datetime.now().isoformat()
                breves_stock.append(breve)

                if len(breves_stock) >= 15:
                    break
        print("✅ Brèves générées automatiquement")
    except Exception as e:
        print("❌ Erreur auto-génération :", e)

# Thread qui exécute fetch_and_generate_breves toutes les 20 minutes
def loop_generer_breves():
    while True:
        fetch_and_generate_breves()
        time.sleep(20 * 60)

# Lancer le thread au démarrage du serveur
threading.Thread(target=loop_generer_breves, daemon=True).start()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
