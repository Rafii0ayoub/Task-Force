import sqlite3
import time

# Importer les fonctions définies précédemment (simulons ici les imports)
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import smtplib

# Initialiser la base de données et créer des tables de test
def init_db():
    conn = sqlite3.connect('crm.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS contacts 
                 (id INTEGER PRIMARY KEY, nom TEXT, email TEXT, reponse TEXT)''')
    conn.commit()
    conn.close()

# Ajout de contact dans la base
def ajouter_contact(nom, email):
    conn = sqlite3.connect('crm.db')
    c = conn.cursor()
    c.execute("INSERT INTO contacts (nom, email) VALUES (?, ?)", (nom, email))
    conn.commit()
    conn.close()

# Mise à jour de la réponse
def mettre_a_jour_reponse(contact_id, reponse):
    conn = sqlite3.connect('crm.db')
    c = conn.cursor()
    c.execute("UPDATE contacts SET reponse = ? WHERE id = ?", (reponse, contact_id))
    conn.commit()
    conn.close()

# Envoi d'un email de test (fictive SMTP pour simplifier)
def envoyer_email(destinataire, sujet, corps):
    print(f"Envoyé à {destinataire}: {sujet}\n{corps}\n")

# Automatisation d'un projet de loi
def generer_projet_de_loi(theme):
    return f"Projet de loi fictif pour le thème '{theme}' : Régulations et propositions spécifiques adaptées à {theme}."

# Automatisation des relances
def relancer_si_non_repondu():
    conn = sqlite3.connect('crm.db')
    c = conn.cursor()
    c.execute("SELECT id, nom, email FROM contacts WHERE reponse IS NULL")
    contacts = c.fetchall()
    
    for contact in contacts:
        envoyer_email(contact[2], "Relance : Demande de rendez-vous",
                      f"Bonjour {contact[1]}, nous souhaitons vous relancer pour un rendez-vous.")
        time.sleep(1)  # pause entre les envois pour ne pas surcharger la sortie
    conn.close()

# Fonction principale
def main():
    # Initialiser la base de données et ajouter des données de test
    init_db()
    print("Base de données initialisée.")

    # Députés fictifs pour les tests
    deputes_test = [
        {"nom": "Rafii Ayoub", "email": "rafii1ayoub@gmail.com"},
        {"nom": "fabrice leroy", "email": "fabrice.leroy.cp95@gmail.com"}
    ]

    # Ajouter les députés dans la base de données
    for depute in deputes_test:
        ajouter_contact(depute["nom"], depute["email"])
    print("Députés ajoutés pour le test.")

    # Générer un projet de loi pour un thème de test
    theme = "transition énergétique"
    projet_de_loi = generer_projet_de_loi(theme)
    print("Projet de loi généré :", projet_de_loi)

    # Envoyer un email de demande de rendez-vous à chaque député
    sujet = "Demande de rendez-vous pour discuter du projet de loi"
    for depute in deputes_test:
        corps = f"Bonjour {depute['nom']},\n\nNous aimerions discuter de notre projet de loi sur le thème : {theme}.\n\n{projet_de_loi}"
        envoyer_email(depute["email"], sujet, corps)

    # Mise à jour fictive de réponse
    mettre_a_jour_reponse(1, "Accepté pour un rendez-vous")
    print("Réponse mise à jour pour le premier député.")

    # Relancer les députés qui n'ont pas répondu
    print("\nLancement de la relance des députés sans réponse.")
    relancer_si_non_repondu()

# Exécuter la fonction principale
if __name__ == "__main__":
    main()