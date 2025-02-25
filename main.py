from fastapi import FastAPI
import requests
import json
import os
from dotenv import load_dotenv
import websocket

# Configuración del clúster
JUPYTERHUB_URL = "https://jupyter.hpca.ual.es/user/ala391"
TOKEN = "23325489c0b54c979ac06e3308771ecf"
HEADERS = {"Authorization": f"token {TOKEN}", "Content-Type": "application/json"}

# Crear la aplicación FastAPI
app = FastAPI()

@app.get("/test")
def test_auth():
    """Verifica si el token de autenticación es válido."""
    session_url = f"{JUPYTERHUB_URL}/api/sessions"
    response = requests.get(session_url, headers=HEADERS)

    if response.status_code == 200:
        return {"message": "Autenticación exitosa", "status": response.status_code}
    else:
        return {"error": "Error en la autenticación", "status": response.status_code, "details": response.text} 