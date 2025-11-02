import redis
import requests
from pymongo import MongoClient

# Redis
redis_client = redis.Redis(host="localhost", port=6379, db=0, decode_responses=True)

# Eventos (Mongo) desde acá por simplicidad (podrías pegarle por HTTP también)
mongo = MongoClient("mongodb://localhost:27017/")
db = mongo["eventflow"]
eventos_col = db["eventos"]
usuarios_col = db["usuarios"]

# Helpers HTTP (si querés consultar servicios por REST)
def get_evento_http(evento_id: str):
    r = requests.get(f"http://127.0.0.1:8002/api/eventos/{evento_id}")
    r.raise_for_status()
    return r.json()

def get_usuario_http(email: str):
    r = requests.get(f"http://127.0.0.1:8001/api/usuarios/{email}")
    r.raise_for_status()
    return r.json()
