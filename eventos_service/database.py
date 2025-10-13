from pymongo import MongoClient

client = MongoClient("mongodb://localhost:27017/")
db = client["eventflow"]
eventos_col = db["eventos"]

eventos_col.create_index([("fecha", 1), ("lugar", 1)])
