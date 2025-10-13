from pymongo import MongoClient

client = MongoClient("mongodb://localhost:27017/")
db = client["eventflow"]
usuarios_col = db["usuarios"]
