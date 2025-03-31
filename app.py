from flask import Flask, jsonify
from flask_cors import CORS
import os
import openai
import feedparser
from datetime import datetime
import threading
import time

app = Flask(__name__)
CORS(app)

# Configuration OpenAI
openai.api_key = os.getenv("OPENAI_API_KEY")

# ✅ Liste complète des flux RSS
RSS_FEEDS = [
    "https://www.topmercato.com/feed/",
    "https://www.footmercato.net/rss",
    "https://www.football.fr/feed/rss",
    "https://www.dailymercato.com/rss",
    "https://www.butfootballclub.fr/rss",
    "https://www.lequipe.fr/rss/actu_rss_Football.xml",
    "https://rmcsport.bfmtv.com/rss/football/",
    "https://www.onzemondial.com/rss",
    "https://www.juventus-fr.com/feed/",
    "https://www.les-transferts.com/feed",
    "https://www.sport.fr/feed",
    "https://www.90min.com/fr/rss",
    "https://www.real-france.fr/feed/",
    "https://www.marca.com/rss/futbol/primera-division.xml",
    "https://as.com/rss/futbol/",
    "https://www.sport.es/rss/",
    "https://www.dailymail.co.uk/sport/football/index.rss",
    "https://www.tuttosport.com/rss/calcio",
    "https://www.abola.pt/rss",
    "https://fabrizioromano.substack.com/feed"
]

# 🏷️ Catégories de clubs
CATEGORIES = {
    "Ligue 1": ["PSG", "OM", "Marseille", "OL", "Lyon", "Monaco", "Lens", "Rennes", "Toulouse", "Nice", "Nantes", "Strasbourg", "Reims"],
    "Liga": ["Barcelone", "Barça", "Real Madrid", "Atletico", "Seville", "Villarreal", "Valence", "La Liga"],
    "Serie A": ["Juventus", "Milan", "Naples", "Inter", "Roma", "Lazio", "Serie A"],
    "Premier League": ["Manchester", "Arsenal", "Chelsea", "Liverpool", "Tottenham", "West Ham", "Newcastle", "Premier League"],
    "Monde": []
}

# Stock en mémoire (à remplacer par base de données si besoin)
breves_stock = []

@app.route("/api/breves")
def get_breves():
    return jsonify(breves_stock)

@app.route("/api/generer", methods=["GET"])
def generer_breves():
    print("🛠️ Génération manuelle déclenchée")
    return jsonify({"ok": True, "nb": generer_briefs_internes()})

def generer_briefs_internes():
    breves_stock.clear()
    articles = []

    for url in RSS_FEEDS:
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries:
                title = entry.title
                content = entry.get("summary", "")
                if len(title) > 10 and len(content) > 20:
                    articles.append({"title": title, "content": content})
        except Exception as e:
            print("⚠️ Erreur RSS:", e)

    articles = articles[:30]
    for art in articles:
        try:
            titre = art["title"]
            contenu = art["content"]
            prompt = f"""
Résume cet article en 400 caractères max dans un style journalistique, sans mention de lien ou site :
Titre : {titre}
Contenu : {contenu}

Réponds au format JSON : 
{{"title": "...", "content": "..."}}
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
        except Exception as e:
            print("Erreur IA:", e)
    print(f"✅ {len(breves_stock)} brèves générées.")
    return len(breves_stock)

# 🔁 Génération automatique toutes les 20 minutes
def boucle_generation():
    while True:
        print("🔁 Génération automatique des brèves")
        generer_briefs_internes()
        time.sleep(1200)  # 20 minutes

if __name__ == "__main__":
    threading.Thread(target=boucle_generation, daemon=True).start()
    app.run(host="0.0.0.0", port=5000)
