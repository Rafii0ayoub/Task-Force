from fastapi import FastAPI
from asgiref.wsgi import WsgiToAsgi  # Pour convertir WSGI vers ASGI

app = FastAPI()

@app.get("/")
def read_root():
    return {"message": "Hello from FastAPI on Vercel without Mangum!"}

# On utilise WsgiToAsgi pour convertir l’application en WSGI.
handler = WsgiToAsgi(app)