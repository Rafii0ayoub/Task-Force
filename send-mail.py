import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import sqlite3
import time
from smtplib import SMTPAuthenticationError

def envoyer_email(destinataire, sujet, corps):
    sender_email = "rafii1ayoub@gmail.com"
    password = "fgzk jaeb hicj vfll"  # Remplacez par le mot de passe d'application généré

    try:
        # Configuration du serveur SMTP
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()  # Démarre la connexion sécurisée
        server.login(sender_email, password)  # Utilisez le mot de passe d'application ici

        # Création du message
        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = destinataire
        msg['Subject'] = sujet
        msg.attach(MIMEText(corps, 'plain'))  # Attache le corps du message

        # Envoi du message
        server.send_message(msg)
        print(f"Email envoyé à {destinataire}")
    except SMTPAuthenticationError:
        print("Erreur : Impossible de s'authentifier. Vérifiez votre adresse e-mail et votre mot de passe.")
    except Exception as e:
        print(f"Une erreur est survenue : {e}")
    finally:
        server.quit()  # Quitte le serveur SMTP

# Exemple d'utilisation
destinataire = "rafii0ayoub@gmail.com"
sujet = "Demande de rendez-vous pour discuter du projet de loi"
corps = "Bonjour, nous souhaiterions discuter de notre projet de loi sur la transition énergétique..."
envoyer_email(destinataire, sujet, corps)