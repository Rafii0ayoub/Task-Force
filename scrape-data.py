import requests
from bs4 import BeautifulSoup

def scrape_deputes_info():
    url = "https://www.assemblee-nationale.fr/dyn/deputes"  # URL fictive pour l'exemple
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # Extraire les informations pertinentes (nom, email, etc.)
    deputes = []
    for dep in soup.select(".depute-info"):
        nom = dep.select_one(".nom").text.strip()
        email = dep.select_one(".email").text.strip() if dep.select_one(".email") else None
        deputes.append({"nom": nom, "email": email})
    return deputes

# Exemple d'utilisation
deputes = scrape_deputes_info()
print(deputes)