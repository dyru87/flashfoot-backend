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

# Liste des flux RSS pour chaque pays
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

# Liste complète des clubs de première division par pays
clubs_par_pays = {
    "Ligue 1": [
        "Angers", "Auxerre", "Brest", "Le Havre", "Lens", "Lille", "Lyon",
        "Marseille", "Monaco", "Montpellier", "Nantes", "Nice", "Paris SG",
        "Reims", "Rennes", "Saint-Étienne", "Strasbourg", "Toulouse"
    ],
    "Liga": [
        "Alavés", "Athletic Bilbao", "Atlético Madrid", "Barcelone", "Betis",
        "Celta Vigo", "Espanyol", "FC Séville", "Getafe", "Girona", "Las Palmas",
        "Leganés", "Mallorca", "Osasuna", "Rayo", "Real Madrid", "Real Sociedad",
        "Real Valladolid", "Valence", "Villarreal"
    ],
    "Serie A": [
        "Atalanta", "Bologne", "Cagliari", "Empoli", "Fiorentina", "Genoa",
        "Hellas Vérone", "Inter Milan", "Juventus", "Lazio", "Lecce", "Milan AC",
        "Naples", "Parme", "Roma", "Salernitana", "Sampdoria", "Sassuolo",
        "Spezia", "Torino", "Udinese", "Venise"
    ],
    "Premier League": [
        "Arsenal", "Aston Villa", "Bournemouth", "Brentford", "Brighton",
        "Chelsea", "Crystal Palace", "Everton", "Fulham", "Ipswich Town",
        "Leicester", "Liverpool", "Manchester City", "Manchester United",
        "Newcastle", "Nottingham Forest", "Southampton", "Tottenham",
        "West Ham", "Wolverhampton"
    ]
}

# Fonction pour détecter la catégorie d'un article en fonction de son titre et de son résumé
def detect_category(title, summary):
    content = f"{title.lower()} {summary.lower()}"
    for category, clubs in clubs_par_pays.items():
        if any(club.lower() in content for club in clubs):
            return category
    return "Monde"

# Fonction pour générer une brève à partir du titre et du résumé d'un article
def generate_breve(title, summary):
    try:
        prompt = (
            f"Écris une brève de football de 300 à 400 caractères, en bon français, à partir du résumé suivant : \n"
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

# Fonction pour récupérer les articles depuis les flux RSS
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

# Fonction pour générer les brèves
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

# Fonction pour planifier la génération automatique des brèves toutes les 20 minutes
def scheduler():
    while True:
        print("\U0001F501 Génération automatique des brèves")
        generate
::contentReference[oaicite:0]{index=0}
 
