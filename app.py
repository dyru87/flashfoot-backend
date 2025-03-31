from flask import Flask, jsonify
from flask_cors import CORS
import os
import openai
import feedparser
from datetime import datetime

app = Flask(__name__)
CORS(app)

# Configuration OpenAI
openai.api_key = os.getenv("OPENAI_API_KEY")  # Met ta vraie clé dans une variable d'environnement

# Liste des flux RSS 
RSS_FEEDS = [
    "https://www.topmercato.com/feed/",
    "https://www.footmercato.net/rss",
    "https://www.football.fr/feed/rss",
    "https://www.dailymercato.com/rss",
    "https://www.butfootballclub.fr/rss"
]

# Catégories par mots-clés
CATEGORIES = {
    "Ligue 1": ["PSG", "OM", "OL", "Monaco", "Lens", "Rennes", "Toulouse"],
    "Liga": ["Barcelone", "Real Madrid", "Atletico", "Seville"],
    "Serie A": ["Juventus", "Milan", "Naples", "Inter"],
    "Premier League": ["Manchester", "Arsenal", "Chelsea", "Liverpool", "Tottenham"],
    "Monde": []
}

# Stock temporaire en mémoire (peut être remplacé par SQLite ensuite)
breves_stock = []


@app.route("/api/breves")
def get_breves():
    return jsonify(breves_stock)


@app.route("/api/generer", methods=["POST"])
def generer_breves():
    breves_stock.clear()
    articles = []

    # Récupération des articles depuis RSS
    for url in RSS_FEEDS:
        feed = feedparser.parse(url)
        for entry in feed.entries:
            articles.append({"title": entry.title, "content": entry.get("summary", "")})

    # Garde les 15 premiers articles valides
    articles = articles[:30]

    for art in articles:
        try:
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
                # Catégorie
                cat = "Monde"
                for nom, mots in CATEGORIES.items():
                    if any(mot.lower() in titre.lower() for mot in mots):
                        cat = nom
                        break

                # Ajout
                breve = eval(texte)
                breve["category"] = cat
                breve["date"] = datetime.now().isoformat()
                breves_stock.append(breve)

                if len(breves_stock) >= 15:
                    break
        except Exception as e:
            print("Erreur IA:", e)

    return jsonify({"ok": True, "nb": len(breves_stock)})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
