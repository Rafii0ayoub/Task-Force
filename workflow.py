import sqlite3

def init_db():
    conn = sqlite3.connect('crm.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS contacts 
                 (id INTEGER PRIMARY KEY, nom TEXT, email TEXT, reponse TEXT)''')
    conn.commit()
    conn.close()

def ajouter_contact(nom, email):
    conn = sqlite3.connect('crm.db')
    c = conn.cursor()
    c.execute("INSERT INTO contacts (nom, email) VALUES (?, ?)", (nom, email))
    conn.commit()
    conn.close()

def mettre_a_jour_reponse(contact_id, reponse):
    conn = sqlite3.connect('crm.db')
    c = conn.cursor()
    c.execute("UPDATE contacts SET reponse = ? WHERE id = ?", (reponse, contact_id))
    conn.commit()
    conn.close()

# Initialiser la base de données
init_db()

# Ajouter un contact et mettre à jour sa réponse
ajouter_contact("Jean Dupont", "jean.dupont@example.com")
mettre_a_jour_reponse(1, "Accepté pour un rendez-vous")