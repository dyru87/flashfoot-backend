from flask import Flask, jsonify, request
from flask_cors import CORS
import feedparser
import openai
import os
from datetime import datetime
import random
import time
import threading

app = Flask(__name__)
CORS(app)

openai.api_key = os.getenv("OPENAI_API_KEY")

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

clubs = {
    "Ligue 1": [
        "psg", "paris", "marseille", "om", "lyon", "nice", "monaco", "lens", "lille", "rennes", "nantes", "reims", "strasbourg",
        "montpellier", "toulouse", "clermont", "metz", "le havre", "auxerre", "angers", "lorient", "brest"
    ],
    "Liga": [
        "barcelone", "real madrid", "atletico", "sevilla", "betis", "valence", "villarreal", "société", "osasuna", "celta",
        "cadix", "mallorca", "granada", "getafe", "alaves", "las palmas", "almeria", "rayo", "girona"
    ],
    "Serie A": [
        "napoli", "juventus", "inter", "milan", "roma", "lazio", "atalanta", "fiorentina", "bologna", "torino", "udinese",
        "lecce", "genoa", "sassuolo", "verona", "empoli", "salernitana", "monza"
    ],
    "Premier League": [
        "chelsea", "arsenal", "manchester united", "man united", "man city", "liverpool", "tottenham", "newcastle",
        "aston villa", "west ham", "everton", "brighton", "fulham", "brentford", "wolves", "bournemouth",
        "nottingham", "luton", "sheffield", "burnley"
    ]
}


def detect_category(title, summary):
    content = f"{title.lower()} {summary.lower()}"
    for cat, keywords in clubs.items():
        if any(kw in content for kw in keywords):
            return cat
    return "Monde"


def generate_breve(title, summary):
    try:
        prompt = (
            f"Écris une brève de football de 300 à 400 caractères, en bon français, à partir du résumé suivant :\n"
            f"{summary}\n"
            f"La brève doit être concise, précise, informative, sans phrases inutiles. Pas de source, pas de lien, pas de site."
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

        content = response.choices[0].message.content.strip()
        return content
    except Exception as e:
        print("Erreur IA: ", e)
        return None


def fetch_articles():
    articles = []
    for url in feeds:
        feed = feedparser.parse(url)
        for entry in feed.entries:
            title = entry.get("title", "")
            summary = entry.get("summary", "")
            if len(summary) > 100:
                articles.append((title, summary))
    return articles


breves = []


def generate_breves():
    global breves
    breves = []
    articles = fetch_articles()
    random.shuffle(articles)
    count = 0
    for title, summary in articles:
        if count >= 15:
            break
        category = detect_category(title, summary)
        content = generate_breve(title, summary)
        if content:
            breves.append({
                "title": title.strip(),
                "content": content,
                "category": category,
                "date": datetime.now().isoformat(" ")
            })
            count += 1
            time.sleep(1)


def scheduler():
    while True:
        print("\U0001F501 Génération automatique des brèves")
        generate_breves()
        time.sleep(20 * 60)  # 20 minutes


@app.route("/api/breves")
def get_breves():
    return jsonify(breves)


@app.route("/api/generer")
def force_generate():
    threading.Thread(target=generate_breves).start()
    return jsonify({"ok": True, "nb": len(breves)})


if __name__ == "__main__":
    threading.Thread(target=scheduler, daemon=True).start()
    app.run(debug=False, host="0.0.0.0")
