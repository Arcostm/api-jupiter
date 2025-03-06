from fastapi import FastAPI
from pydantic import BaseModel
import requests
import json
import time
import websocket
import threading

# uvicorn main:app --reload
# Configuración del clúster
JUPYTERHUB_URL = "https://jupyter.hpca.ual.es/user/ala391"
TOKEN = "23325489c0b54c979ac06e3308771ecf"
HEADERS = {"Authorization": f"token {TOKEN}", "Content-Type": "application/json"}

# Crear la aplicación FastAPI
app = FastAPI()

# Modelo de datos para recibir kernel_id y comando
class ExecuteRequest(BaseModel):
    kernel_id: str
    command: str

# Variable global para almacenar el resultado del comando
result = None

# Función para manejar mensajes WebSocket
def on_message(ws, message):
    print(f"Mensaje recibido: {message}")
    global result
    msg = json.loads(message)
    if msg['msg_type'] == 'stream':
        result = msg['content']['text']
    elif msg['msg_type'] == 'execute_result':
        result = msg['content']['data']['text/plain']

def on_error(ws, error):
    print(f"WebSocket error: {error}")

def on_close(ws, close_status_code, close_msg):
    print("WebSocket closed")

def on_open(ws):
    print("WebSocket connection established")



@app.get("/test")
def test_auth():
    """Verifica si el token de autenticación es válido."""
    session_url = f"{JUPYTERHUB_URL}/api/sessions"
    response = requests.get(session_url, headers=HEADERS)

    if response.status_code == 200:
        return {"message": "Autenticación exitosa", "status": response.status_code}
    else:
        return {"error": "Error en la autenticación", "status": response.status_code, "details": response.text}

@app.post("/create_kernel")
def create_kernel():
    """Crea un nuevo kernel en Jupyter."""
    kernel_url = f"{JUPYTERHUB_URL}/api/kernels"
    response = requests.post(kernel_url, headers=HEADERS)

    if response.status_code == 201:
        return {"message": "Kernel creado", "kernel_id": response.json()["id"]}
    else:
        return {"error": "No se pudo crear el kernel", "status": response.status_code, "details": response.text}

@app.get("/check_kernels")
def check_kernels():
    """Verifica si se pueden listar los kernels disponibles."""
    kernel_url = f"{JUPYTERHUB_URL}/api/kernels"
    response = requests.get(kernel_url, headers=HEADERS)

    return {"status": response.status_code, "response": response.json() if response.status_code == 200 else response.text}

@app.post("/execute_command")
def execute_command(request: ExecuteRequest):
    """Ejecuta un comando en un kernel específico."""
    global result
    result = None

    # URL del WebSocket del kernel
    ws_url = f"wss://jupyter.hpca.ual.es/user/ala391/api/kernels/{request.kernel_id}/channels"
    
    # Establecer conexión WebSocket
    ws = websocket.WebSocketApp(ws_url,
                                header=HEADERS,
                                on_message=on_message,
                                on_error=on_error,
                                on_close=on_close)
    ws.on_open = on_open

    # Iniciar la conexión WebSocket en un hilo separado
    wst = threading.Thread(target=ws.run_forever)
    wst.start()

    # Esperar a que la conexión WebSocket esté lista
    time.sleep(2)

    # Enviar el comando al kernel
    msg = {
        "header": {
            "msg_id": "execute_" + str(int(time.time())),
            "username": "user",
            "session": "session_id",
            "msg_type": "execute_request",
            "version": "5.3"
        },
        "parent_header": {},
        "metadata": {},
        "content": {
            "code": request.command,
            "silent": False,
            "store_history": True,
            "user_expressions": {},
            "allow_stdin": False
        }
    }
    ws.send(json.dumps(msg))

    # Esperar a que el comando se ejecute y se reciba la respuesta
    time.sleep(2)

    # Cerrar la conexión WebSocket
    ws.close()

    # Devolver el resultado
    return {"result": result}