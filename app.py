from flask import Flask, jsonify, request
from flask_cors import CORS
from datetime import datetime
import feedparser
import json
import os
import time
import threading
import openai
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
CORS(app)

openai.api_key = os.getenv("OPENAI_API_KEY")

BREVES_FILE = "breves.json"

RSS_FEEDS = [
    # France
    "https://www.lequipe.fr/rss/actu_rss_Football.xml",
    "https://www.footmercato.net/rss",
    "https://www.football.fr/feed",
    "https://www.butfootballclub.fr/rss.xml",
    "https://www.les-transferts.com/feed",
    "https://www.topmercato.com/feed",
    "https://www.dailymercato.com/rss",
    "https://www.onzemondial.com/rss",
    "https://www.foot-sur7.fr/feed",

    # Espagne
    "https://as.com/rss/futbol/",
    "https://www.marca.com/en/rss.xml",
    "https://www.sport.es/rss",
    "https://www.real-france.fr/feed/",

    # Italie
    "https://www.tuttosport.com/rss/calcio.xml",
    "https://www.juventus-fr.com/feed/",

    # Angleterre
    "https://www.dailymail.co.uk/sport/index.rss",
    "https://www.90min.com/rss",

    # Monde
    "https://rmcsport.bfmtv.com/rss/football/",
    "https://www.abola.pt/rss",
    "https://www.fabrizioromano.com/feed/",
    "https://www.tntsports.co.uk/rss.xml",
    "https://www.football365.fr/feed/rss"
]

CATEGORIES = {
    "france": "Ligue 1",
    "espagne": "Liga",
    "italie": "Serie A",
    "angleterre": "PL",
    "monde": "Monde"
}

def get_category_from_url(url):
    for keyword, category in CATEGORIES.items():
        if keyword in url:
            return category
    return "Monde"

def generate_brief(title, summary):
    prompt = f"Rédige une brève d’environ 350 caractères, espaces compris, dans un style journalistique, basée sur ce titre et ce résumé :\nTitre : {title}\nRésumé : {summary}"
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "Tu es un journaliste sportif."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=300
        )
        texte = response.choices[0].message.content.strip()
        if 300 <= len(texte) <= 400:
            return texte
        else:
            return None
    except Exception as e:
        print("Erreur IA:", e)
        return None

def load_breves():
    if os.path.exists(BREVES_FILE):
        with open(BREVES_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def save_breves(breves):
    with open(BREVES_FILE, "w", encoding="utf-8") as f:
        json.dump(breves, f, ensure_ascii=False, indent=2)

def generate_breves_from_rss(limit=15):
    breves = load_breves()
    titles_seen = {b["title"] for b in breves}
    nouvelles_breves = []

    for url in RSS_FEEDS:
        feed = feedparser.parse(url)
        category = get_category_from_url(url)
        for entry in feed.entries:
            if len(nouvelles_breves) >= limit:
                break
            if entry.title in titles_seen:
                continue
            content = generate_brief(entry.title, entry.summary)
            if content:
                nouvelle = {
                    "title": entry.title,
                    "content": content,
                    "date": str(datetime.utcnow()),
                    "category": category
                }
                nouvelles_breves.append(nouvelle)
                titles_seen.add(entry.title)

    if nouvelles_breves:
        breves = nouvelles_breves + breves
        save_breves(breves)
    return len(nouvelles_breves)

@app.route("/api/breves")
def api_breves():
    return jsonify(load_breves())

@app.route("/api/generer")
def api_generer():
    nb = generate_breves_from_rss()
    return jsonify({"ok": True, "nb": nb})

def start_scheduler():
    def job():
        while True:
            print("🔁 Génération automatique des brèves")
            generate_breves_from_rss()
            time.sleep(1200)

    threading.Thread(target=job, daemon=True).start()

start_scheduler()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
