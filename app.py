from flask import Flask, jsonify, request
from flask_cors import CORS
import feedparser
import openai
import os
from datetime import datetime, timedelta
import random
import time
import threading
from collections import defaultdict

app = Flask(__name__)
CORS(app)

openai.api_key = os.getenv("OPENAI_API_KEY")

# ========== CONFIGURATION ==========
MAX_REQUESTS_PER_HOUR = 5
REQUEST_LOG = defaultdict(list)  # IP -> [timestamps]
CACHE_DURATION_MINUTES = 30

# Cache pour éviter les doublons
article_cache = set()  # titre+summary utilisés récemment

feeds = [
    # France
    "https://www.lequipe.fr/rss/actu_rss_Football.xml",
    "https://www.footmercato.net/rss",
    "https://www.butfootballclub.fr/rss.xml",
    "https://www.foot01.com/rss",
    "https://www.les-transferts.com/feed",
    # Espagne
    "https://www.realmadridnews.com/feed/",
    "https://www.fcbarcelonanoticias.com/rss",
    "https://www.mundodeportivo.com/rss/futbol",
    "https://www.sport.es/rss/futbol.xml",
    "https://as.com/rss/tags/futbol/primera_division/a.xml",
    # Italie
    "https://www.calciomercato.com/rss",
    "https://www.tuttomercatoweb.com/rss",
    "https://www.football-italia.net/rss.xml",
    "https://www.juventusnews24.com/feed/",
    "https://www.gazzetta.it/rss/home.xml",
    "https://www.romapress.net/feed/",
    "https://sempremilan.com/feed",
    "https://www.lalaziosiamonoi.it/rss.xml",
    "https://www.inter-news.it/feed/",
    "https://napolipiu.com/feed",
    # Angleterre
    "https://www.chelseafc.com/en/news/latest-news.rss",
    "https://www.arsenal.com/rss-feeds/news",
    "https://www.manchestereveningnews.co.uk/all-about/manchester-united-fc/?service=rss",
    "https://www.liverpoolfc.com/news/rss-feeds",
    "https://www.mirror.co.uk/sport/football/rss.xml",
    # Monde
    "https://www.fifa.com/rss-feeds/news",
    "https://www.goal.com/feeds/en/news",
    "https://www.espn.com/espn/rss/soccer/news",
    "https://www.si.com/rss/si_soccer.rss",
    "https://www.skysports.com/rss/12040"
]

categories = ["Ligue 1", "Liga", "Serie A", "Premier League", "Monde"]
breves = []

def detect_category(title, summary):
    content = f"{title.lower()} {summary.lower()}"
    if any(x in content for x in ["psg", "lens", "ligue 1", "marseille", "rennes", "nantes"]):
        return "Ligue 1"
    if any(x in content for x in ["barcelone", "madrid", "liga", "atletico", "real", "espagne"]):
        return "Liga"
    if any(x in content for x in ["napoli", "milan", "inter", "serie a", "italie", "juventus"]):
        return "Serie A"
    if any(x in content for x in ["chelsea", "manchester", "arsenal", "liverpool", "premier league", "angleterre"]):
        return "Premier League"
    return "Monde"

def generate_breve(title, summary):
    try:
        prompt = (
            f"Écris une brève de football de 300 à 400 caractères, en bon français, à partir du résumé suivant :\n"
            f"{summary}\n"
            f"La brève doit être concise, précise, informative, sans phrases inutiles. Pas de source, pas de lien."
        )
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "Tu es un journaliste sportif français."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=220,
            temperature=0.7,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print("[ERREUR IA]", e)
        return None

def fetch_articles():
    articles = []
    for url in feeds:
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries:
                title = entry.get("title", "").strip()
                summary = entry.get("summary", "").strip()
                if len(summary) > 100 and (title + summary) not in article_cache:
                    articles.append((title, summary))
        except Exception as e:
            print(f"[ERREUR RSS] {url}: {e}")
    return articles

def generate_breves():
    global breves
    breves = []
    articles = fetch_articles()
    random.shuffle(articles)
    count = 0
    for title, summary in articles:
        if count >= 15:
            break
        content = generate_breve(title, summary)
        if content:
            category = detect_category(title, summary)
            key = title + summary
            article_cache.add(key)
            breves.append({
                "title": title,
                "content": content,
                "category": category,
                "date": datetime.now().isoformat(" "),
                "views": random.randint(10000, 120000)
            })
            count += 1
            time.sleep(1)

    # Nettoyer le cache des articles trop anciens
    if len(article_cache) > 300:
        article_cache.clear()
        print("[CACHE] Réinitialisé après 300 articles.")

def scheduler():
    while True:
        print("\U0001F501 Génération automatique des brèves à", datetime.now().strftime("%H:%M"))
        generate_breves()
        time.sleep(20 * 60)

@app.route("/api/breves")
def get_breves():
    return jsonify(breves)

@app.route("/api/generer")
def force_generate():
    ip = request.remote_addr
    now = datetime.now()
    # Nettoyer les anciennes entrées
    REQUEST_LOG[ip] = [ts for ts in REQUEST_LOG[ip] if now - ts < timedelta(hours=1)]
    if len(REQUEST_LOG[ip]) >= MAX_REQUESTS_PER_HOUR:
        return jsonify({"ok": False, "error": "Trop de requêtes. Réessayez plus tard."}), 429
    REQUEST_LOG[ip].append(now)
    threading.Thread(target=generate_breves).start()
    return jsonify({"ok": True, "nb": len(breves)})

if __name__ == "__main__":
    threading.Thread(target=scheduler, daemon=True).start()
    app.run(debug=False, host="0.0.0.0")
