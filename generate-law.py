import openai

openai.api_key = "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"

def generer_projet_de_loi(theme):
    prompt = f"Rédige un projet de loi pour le thème : {theme}. Inclure des objectifs et des propositions spécifiques."
    response = openai.Completion.create(
        engine="gpt-4o-mini-2024-07-18",  
        prompt=prompt,
        max_tokens=500
    )
    return response.choices[0].text.strip()

# Exemple d'utilisation
theme = "augmentation du temps de travail"
projet_de_loi = generer_projet_de_loi(theme)
print(projet_de_loi)

generer_projet_de_loi("transition énérgitique")