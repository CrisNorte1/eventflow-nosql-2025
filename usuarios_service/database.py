from pymongo import MongoClient

client = MongoClient("mongodb://localhost:27017/")  # Definimos el cliente de MongoDB
db = client["eventflow"]
usuarios_col = db["usuarios"]
usuarios_col.create_index("email", unique=True)
