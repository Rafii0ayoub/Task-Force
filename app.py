from flask import Flask, render_template, request, redirect, url_for, flash
import sqlite3
import openai
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from dotenv import load_dotenv
import os
import pandas as pd
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from flask_dance.contrib.google import make_google_blueprint, google

# Charger les variables d'environnement
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY')  # Utilise la clé secrète du fichier .env

# Configuration de Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

# Simuler une base de données d'utilisateurs
users = {}

class User(UserMixin):
    def __init__(self, username):
        self.id = username

@login_manager.user_loader
def load_user(user_id):
    return User(user_id)

API_KEY = "AIzaSyDaMc_e9NPwDsSBb3_D4tw2-8P4rqeYQj8"
CLIENT_ID= "946394220088-3mlr534ugu544aui0j142c7bcrj89go8.apps.googleusercontent.com"
CLIENT_SECRET= "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"

google_bp = make_google_blueprint(client_id=CLIENT_ID, client_secret=CLIENT_SECRET, redirect_to='google.login')
app.register_blueprint(google_bp, url_prefix='/google_login')

@app.route('/google_login')
def google_login():
    if not google.authorized:
        return redirect(url_for('google.login'))
    resp = google.get('/plus/v1/people/me')
    assert resp.ok, resp.text
    return f"You are logged in as: {resp.json()['displayName']}"


# Configuration de la base de données
def create_table():
    conn = sqlite3.connect('deputes.db')
    cursor = conn.cursor()

    # Création de la table des députés
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS deputes (
            identifiant TEXT PRIMARY KEY,
            prenom TEXT,
            nom TEXT,
            region TEXT,
            departement TEXT,
            numero_circonscription INTEGER,
            profession TEXT,
            groupe_politique_complet TEXT,
            groupe_politique_abrege TEXT,
            email TEXT
        )
    ''')
    print("Table 'deputes' créée ou déjà existante.")

    # Création de la table des lois
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS lois (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            titre TEXT NOT NULL,
            date TEXT,
            depute_proposant TEXT
        )
    ''')
    print("Table 'lois' créée ou déjà existante.")

    # Création de la table des rendez-vous
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS rendez_vous (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            depute_id TEXT NOT NULL,
            date_rdv DATE NOT NULL,
            heure_rdv TIME NOT NULL,
            lieu TEXT NOT NULL,
            objet TEXT NOT NULL,
            notes TEXT,
            FOREIGN KEY (depute_id) REFERENCES deputes (identifiant) ON DELETE CASCADE
        );
    ''')
    print("Table 'rendez_vous' créée ou déjà existante.")

    # Création de la table des échanges
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS journal_echanges (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            depute_id TEXT NOT NULL,
            type_echange TEXT NOT NULL,
            details TEXT,
            FOREIGN KEY (depute_id) REFERENCES deputes (identifiant) ON DELETE CASCADE
        )
    ''')
    print("Table 'journal_echanges' créée ou déjà existante.")

    conn.commit()
    conn.close()

users = {
    "admin": "password123", 
     "contact@tesla-mag.com": "password123" # Exemple d'utilisateur, changez les identifiants pour la production
}

# Fonction pour nettoyer les textes et générer les e-mails sans accents ni caractères spéciaux
def nettoyer_texte(texte):
    if isinstance(texte, str):
        texte = texte.replace("�", "é")  # Supprime les accents
        texte = texte.replace("'", " ")   # Remplace les apostrophes par des espaces
        texte = texte.replace("/", "-")    # Remplace les slashes par des tirets
        return texte
    return texte

def import_data_from_csv(csv_file):
    # Lecture du fichier CSV
    df = pd.read_csv(csv_file, sep=';', encoding='utf-8')
    # Nettoyer les colonnes et générer l'adresse e-mail
    df['prenom'] = df['prenom'].apply(nettoyer_texte)
    df['nom'] = df['nom'].apply(nettoyer_texte)
    df['email'] = df['prenom'].str.lower().str.replace(" ", "") + '.' + df['nom'].str.lower().str.replace(" ", "") + '@assemblee-nationale.fr'

    # Connexion à la base de données
    conn = sqlite3.connect('deputes.db')
    cursor = conn.cursor()

    # Insérer chaque ligne du DataFrame dans la base de données
    for index, row in df.iterrows():
        try:
            cursor.execute('''
                INSERT OR IGNORE INTO deputes (
                    identifiant, 
                    prenom, 
                    nom, 
                    region, 
                    departement, 
                    numero_circonscription, 
                    profession, 
                    groupe_politique_complet, 
                    groupe_politique_abrege,
                    email
                ) 
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                row['identifiant'], 
                row['prenom'], 
                row['nom'], 
                row['region'], 
                row['departement'], 
                row['numero_circonscription'], 
                row['profession'], 
                row['groupe_politique_complet'], 
                row['groupe_politique_abrege'],
                row['email']
            ))
        except sqlite3.Error as e:
            print(f"Erreur lors de l'insertion de l'identifiant {row['identifiant']}: {e}")

    conn.commit()
    conn.close()

# Fonction pour récupérer la liste des députés
def get_deputes():
    conn = sqlite3.connect('deputes.db')
    c = conn.cursor()
    c.execute("SELECT * FROM deputes")
    deputes = c.fetchall()
    conn.close()
    return deputes

# Fonction pour envoyer un email
def envoyer_email(destinataire, sujet, corps):
    sender_email = os.getenv('SENDER_EMAIL')
    password = os.getenv('EMAIL_PASSWORD')

    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(sender_email, password)

        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = destinataire
        msg['Subject'] = sujet
        msg.attach(MIMEText(corps, 'plain'))

        server.send_message(msg)
        print(f"Email envoyé à {destinataire}")
    except Exception as e:
        print(f"Une erreur est survenue : {e}")
    finally:
        server.quit()

# Fonction pour générer un projet de loi
openai.api_key = os.getenv('OPENAI_API_KEY')

import openai
import os

openai.api_key = os.getenv("OPENAI_API_KEY")

def generer_projet_de_loi(theme):
    messages = [
        {"role": "system", "content": "Vous êtes un assistant utile spécialisé dans la rédaction de projets de loi."},
        {"role": "user", "content": f"Rédige un projet de loi pour le thème : {theme}. Inclure des objectifs et des propositions spécifiques."}
    ]
    
    response = openai.ChatCompletion.create(
        model="gpt-4",  # Spécifiez le modèle ici
        messages=messages,
        max_tokens=500
    )
    
    return response.choices[0].message['content'].strip()


def envoyer_email(destinataire, sujet, corps):
    sender_email = os.getenv('SENDER_EMAIL')
    password = os.getenv('EMAIL_PASSWORD')

    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(sender_email, password)

        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = destinataire
        msg['Subject'] = sujet
        msg.attach(MIMEText(corps, 'plain'))

        server.send_message(msg)
        flash(f"Email envoyé à {destinataire}")
    except Exception as e:
        flash(f"Une erreur est survenue lors de l'envoi de l'email : {e}")
    finally:
        server.quit()

# Route pour afficher le formulaire d'envoi d'email et gérer l'envoi
@app.route('/send_email', methods=['GET', 'POST'])
@login_required  # S'assurer que l'utilisateur est connecté
def send_email():
    if request.method == 'POST':
        destinataire = request.form['destinataire']
        sujet = request.form['sujet']
        corps = request.form['corps']
        
        # Envoyer l'email avec la fonction `envoyer_email`
        envoyer_email(destinataire, sujet, corps)
        return redirect(url_for('index'))  # Redirection après envoi

    # Afficher le formulaire d'envoi d'email
    return render_template('send_email.html')

# Route pour la connexion
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        # Vérification du nom d'utilisateur et du mot de passe
        if username in users and users[username] == password:  # Vérification simple
            user = User(username)
            login_user(user)
            return redirect(url_for('index'))  # Rediriger vers index.html après connexion
        else:
            flash('Nom d’utilisateur ou mot de passe incorrect.')
    return render_template('login.html')

# Route pour la page d'accueil
@app.route('/')
@login_required  # Exige que l'utilisateur soit connecté
def index():
    return render_template('index.html')

# Route pour la déconnexion
@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))


@app.route('/add_contact', methods=['GET', 'POST'])
@login_required 
def add_contact():
    if request.method == 'POST':
        nom = request.form['nom']
        email = request.form['email']
        conn = sqlite3.connect('deputes.db')
        c = conn.cursor()
        c.execute("INSERT INTO deputes (nom, email) VALUES (?, ?)", (nom, email))
        conn.commit()
        conn.close()
        flash('Contact ajouté avec succès !')
        return redirect(url_for('index'))
    return render_template('add_contact.html')

@app.route('/view_contacts')
@login_required 
def view_contacts():
    deputes = get_deputes()
    return render_template('view_contacts.html', deputes=deputes)

@app.route('/generate_bill', methods=['GET', 'POST'])
@login_required 
def generate_bill():
    if request.method == 'POST':
        theme = request.form['theme']
        projet_de_loi = generer_projet_de_loi(theme)
        return render_template('generate_bill.html', projet_de_loi=projet_de_loi, theme=theme)
    return render_template('generate_bill.html')

@app.route('/depute_detail/<string:depute_id>')  # Utilisez string pour correspondre à l'identifiant
@login_required 
def depute_detail(depute_id):
    conn = sqlite3.connect('deputes.db')  # Assurez-vous que vous utilisez le bon nom de base de données
    c = conn.cursor()
    
    # Récupérer les informations du député
    c.execute("SELECT * FROM deputes WHERE identifiant = ?", (depute_id,))
    depute = c.fetchone()

    # Vérifiez si le député existe avant de continuer
    if depute is None:
        flash("Député non trouvé.")
        return redirect(url_for('view_contacts'))  # Ou une autre route appropriée

    # Récupérer les échanges et rendez-vous pour ce député
    c.execute("SELECT * FROM journal_echanges WHERE depute_id = ?", (depute_id,))
    echanges = c.fetchall()

    c.execute("SELECT * FROM lois WHERE depute_proposant = ?", (depute[1],))  # Assume que le nom est dans la colonne 1
    lois = c.fetchall()

    conn.close()
    return render_template('depute_detail.html', depute=depute, echanges=echanges, lois=lois)  # Passez l'objet de député à la vue

def insert_sample_journal_echange():
    conn = sqlite3.connect('deputes.db')
    c = conn.cursor()

    # Sample exchanges to insert
    exchanges = [
        ("2024-01-20", "795998", "Réunion avec Émeline K/Bidi pour discuter de la loi sur l'environnement.", "réunion"),
        ("2024-02-15", "796106", "Email envoyé à Édouard Bénard concernant la réforme des retraites.", "email"),
        ("2024-03-01", "795998", "Discussion informelle avec Émeline sur les priorités législatives.", "discussion"),
        ("2024-03-10", "796106", "Réunion avec le groupe parlementaire pour discuter des propositions.", "réunion"),
        ("2024-04-05", "795998", "Échange d'idées sur l'éducation numérique par email.", "email"),
    ]

    # Insert sample exchanges into the `journal_echange` table
    c.executemany('''
        INSERT INTO journal_echanges (date, depute_id, type_echange, details) VALUES (?, ?, ?, ?)
    ''', exchanges)

    conn.commit()
    conn.close()



def insert_sample_lois():
    conn = sqlite3.connect('deputes.db')
    c = conn.cursor()

    # Sample laws to insert
    lois = [
        ("Loi sur la protection de l'environnement", "2024-01-15", "Émeline K/Bidi"),
        ("Loi sur la réforme des retraites", "2024-03-22", "Édouard Bénard"),
        ("Loi sur l'éducation numérique", "2024-04-10", "Louis Dupont"),
        ("Loi sur la sécurité intérieure", "2024-05-05", "Sophie Durand"),
        ("Loi sur la santé publique", "2024-06-12", "Pierre Martin"),
    ]

    # Insert sample laws into the `lois` table
    c.executemany('''
        INSERT INTO lois (titre, date, depute_proposant) VALUES (?, ?, ?)
    ''', lois)

    conn.commit()
    conn.close()

def insert_rdv():
    conn = sqlite3.connect('crm.db')  # Make sure to replace 'crm.db' with your actual database filename
    c = conn.cursor()

    # Sample data for the rendez-vous
    rendez_vous_data = [
    (1, '2024-10-30', '09:00', 'Bureau du Député', 'Discussion sur la loi sur l\'éducation', 'Préparer le dossier'),
    (2, '2024-11-01', '14:00', 'Salle de conférence', 'Réunion sur le budget', 'Inviter les membres du comité'),
    (1, '2024-11-05', '11:30', 'Bureau du Député', 'Entretien avec les citoyens', 'Préparer les questions'),
    (3, '2024-11-10', '15:00', 'Zoom', 'Séance d\'information sur le projet de loi', 'Envoyer le lien aux participants'),
    (2, '2024-11-15', '10:00', 'Bureau de la mairie', 'Rencontre avec le maire', 'Préparer le discours'),
    (1, '2024-11-20', '13:30', 'Bureau du Député', 'Réunion sur les priorités législatives', 'Apporter des statistiques'),
    (3, '2024-11-25', '16:00', 'Café du coin', 'Discussion informelle avec les électeurs', 'Prendre des notes'),
    (2, '2024-11-30', '09:00', 'Bureau du Député', 'Analyse des retours des électeurs', 'Mettre à jour le rapport'),
    (1, '2024-12-05', '14:00', 'Salle des fêtes', 'Rassemblement communautaire', 'Organiser des activités'),
    (3, '2024-12-10', '11:00', 'Bureau du Député', 'Réunion avec le groupe de travail', 'Revoir les objectifs'),
    ]

     # Insert the rendez-vous data into the database
    for rdv in rendez_vous_data:
      c.execute('''
      INSERT INTO rendez_vous (depute_id, date_rdv, heure_rdv, lieu, objet, notes)
      VALUES (?, ?, ?, ?, ?, ?)
      ''', rdv)

    # Commit the changes and close the connection
    conn.commit()
    conn.close()


@app.route('/dashboard')
def dashboard():
    conn = sqlite3.connect('deputes.db')
    c = conn.cursor()

    # Calcul des KPI
    c.execute("SELECT COUNT(*) FROM deputes")
    total_deputes = c.fetchone()[0]

    c.execute("SELECT COUNT(*) FROM lois")
    total_lois = c.fetchone()[0]

    c.execute("SELECT COUNT(*) FROM journal_echanges")
    total_echanges = c.fetchone()[0]

    c.execute("SELECT COUNT(*) FROM rendez_vous")
    total_rdv = c.fetchone()[0]

    # Répartition des députés par région
    c.execute("SELECT region, COUNT(*) FROM deputes GROUP BY region")
    deputes_par_region = c.fetchall()

    # Derniers projets de loi
    c.execute("SELECT titre, date, depute_proposant FROM lois ORDER BY date DESC LIMIT 5")
    lois_recents = c.fetchall()

    conn.close()

    return render_template('dashboard.html', 
                           total_deputes=total_deputes,
                           total_lois=total_lois,
                           total_echanges=total_echanges,
                           total_rdv=total_rdv,
                           deputes_par_region=deputes_par_region,
                           lois_recents=lois_recents)
@app.route('/article/<int:article_id>')
def article_detail(article_id):
    # Exemple de données d'articles, cela peut être remplacé par une base de données
    articles = {
        1: {
            'title': "Comprendre la transition énergétique",
            'content': "Cet article explique les enjeux de la transition énergétique, ses objectifs, et les politiques à adopter pour y parvenir."
        },
        2: {
            'title': "Le rôle des législateurs dans la transition énergétique",
            'content': "Dans cet article, nous examinons comment les législateurs peuvent influencer et faciliter la transition énergétique."
        },
        3: {
            'title': "Innovations législatives pour un avenir durable",
            'content': "Cet article présente des exemples d'innovations législatives qui favorisent la durabilité et l'environnement."
        }
    }
    
    article = articles.get(article_id)
    if article:
        return render_template('article_detail.html', article=article)
    else:
        return "Article non trouvé", 404
    

# Initialisation de la base de données et importation des données
create_table()
import_data_from_csv('liste_deputes_excel.csv')


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=8080, debug=True)
