from pymongo import MongoClient
import os
from dotenv import load_dotenv

load_dotenv()


# connect to mongo atlas cluster
mongo_client = MongoClient(os.getenv("MONGO_URI"))

# access database
movie_finder_db = mongo_client["movie_finder_db "]

# pick a code to operate on
movies_collection = movie_finder_db["movies"]
