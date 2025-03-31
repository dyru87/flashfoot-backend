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

breves = []
cache_articles = set()

def detect_category(title, summary):
    content = f"{title.lower()} {summary.lower()}"
    if any(x in content for x in [
        "psg", "marseille", "lyon", "lens", "monaco", "rennes", "nice", "nantes", "reims",
        "strasbourg", "toulouse", "clermont", "montpellier", "le havre", "metz", "lorient", "brest"
    ]):
        return "Ligue 1"
    if any(x in content for x in [
        "real", "barcelone", "atletico", "sevilla", "villarreal", "betis", "valence", "cadiz",
        "alaves", "getafe", "celta", "osasuna", "mallorca", "rayo", "granada", "las palmas",
        "girona", "athletic"
    ]):
        return "Liga"
    if any(x in content for x in [
        "juventus", "napoli", "milan", "inter", "roma", "lazio", "atalanta", "fiorentina", "torino",
        "bologna", "lecce", "genoa", "cagliari", "empoli", "sassuolo", "verona", "salernitana", "monza"
    ]):
        return "Serie A"
    if any(x in content for x in [
        "manchester", "liverpool", "arsenal", "chelsea", "tottenham", "aston villa", "west ham",
        "newcastle", "brighton", "wolves", "crystal palace", "brentford", "everton", "fulham",
        "nottingham", "bournemouth", "sheffield", "luton", "burnley"
    ]):
        return "Premier League"
    return "Monde"

def generate_title(summary):
    try:
        prompt = (
            "Génère un titre journalistique en français (max 100 caractères), accrocheur et clair, "
            "pour une brève de football basée sur le texte suivant :\n"
            f"{summary}\n"
            "Pas de nom de site, pas de source, pas de lien. En français uniquement."
        )
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "Tu es un journaliste sportif français."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=80,
            temperature=0.8,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print("Erreur génération titre :", e)
        return "Titre non disponible"

def generate_breve(title, summary):
    try:
        prompt = (
            "Écris une brève de football de 380 à 420 caractères, en bon français, à partir du résumé suivant :\n"
            f"{summary}\n"
            "La brève doit être concise, précise, informative. Pas de source, pas de lien, pas de site."
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
        print("Erreur génération brève :", e)
        return None

def fetch_articles():
    articles = []
    for url in feeds:
        feed = feedparser.parse(url)
        for entry in feed.entries:
            title = entry.get("title", "")
            summary = entry.get("summary", "")
            if len(summary) > 100 and (title, summary) not in cache_articles:
                cache_articles.add((title, summary))
                articles.append((title, summary))
    return articles

def generate_breves():
    global breves
    articles = fetch_articles()
    random.shuffle(articles)
    new_breves = []
    for title, summary in articles:
        if len(new_breves) >= 15:
            break
        category = detect_category(title, summary)
        content = generate_breve(title, summary)
        titre_fr = generate_title(summary)
        if content and titre_fr:
            new_breves.append({
                "title": titre_fr,
                "content": content,
                "category": category,
                "date": datetime.now().isoformat(" "),
                "views": random.randint(10000, 120000)
            })
        time.sleep(1)

    if new_breves:
        breves = new_breves
    else:
        print("⚠️ Aucune brève générée, conservation des anciennes.")

def scheduler():
    while True:
        print("🔁 Génération automatique des brèves à", datetime.now().strftime("%H:%M"))
        generate_breves()
        time.sleep(20 * 60)

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
