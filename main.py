from fastapi import FastAPI, HTTPException, status
from db import movies_collection
from pydantic import BaseModel
from bson.objectid import ObjectId
from utils import replace_mongo_id
import requests


app = FastAPI()

OMDbAPI_url = "http://www.omdbapi.com/?i=tt3896198&apikey=72cdd2f4"
OMDB_api_key = "72cdd2f4"


class FavMovie(BaseModel):
    title: str
    genre: str
    year: int
    imdb_ID: str
    user_rating: int


@app.get("/")
def home_page():
    return {"message": "Welcome to our home page"}


@app.get("/movies/{title}")
def search_movies(title="", genre="", limit=10, skip=0):
    movies = movies_collection.find(
        filter={
            "$or": [
                {"title": {"$regex": title, "$options": "i"}},
                {"genre": {"$regex": genre, "$options": "i"}},
            ]
        },
        limit=int(limit),
        skip=int(skip),
    ).to_list()

    # Return response
    return {"data": list(map(replace_mongo_id, movies))}


@app.post("/favorites")
def save_favorite(movie: FavMovie):
    movies_collection.insert_one(movie.model_dump())
    return {"message": "movie added successfully."}


@app.get("/favorites/top-3")
def top_3_favorites():
    pass
