from fastapi import FastAPI, HTTPException, status
from db import movies_collection
from pydantic import BaseModel
from utils import replace_mongo_id
import requests
import os
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

OMDB_API_URL = os.getenv("OMDB_API_URL")
OMDB_API_KEY = os.getenv("OMDB_API_KEY")


class FavMovie(BaseModel):
    title: str
    genre: str
    year: int
    imdb_ID: str
    user_rating: float


@app.get("/")
def home_page():
    return {"message": "Welcome to Movie Finder!"}


@app.get("/movies/{title}")
def search_movies_by_title(title: str):
    if not OMDB_API_URL or not OMDB_API_KEY:
        raise HTTPException(status_code=500, detail="OMDb API credentials missing")

    query_params = {"t": title, "apikey": OMDB_API_KEY}
    response = requests.get(OMDB_API_URL, params=query_params)

    if response.status_code != 200:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error fetching data from OMDb API",
        )

    movie = response.json()

    if movie.get("Response") == "False":
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"sorry, movie '{title}' not found",
        )

    return {
        "title": movie.get("Title"),
        "year": movie.get("Year"),
        "genre": movie.get("Genre", "N/A"),
        "imdbID": movie.get("imdbID"),
    }


@app.post("/favorites")
def save_favorite(movie: FavMovie):
    movies_collection.insert_one(movie.model_dump())
    return {"message": "movie added successfully."}


@app.get("/favorites")
def list_favorites():
    movies = list(movies_collection.find())
    return [replace_mongo_id(movie) for movie in movies]


@app.get("/favorites/top-3")
def top_3_favorites():
    top_movies = movies_collection.find().sort("user_rating", -1).limit(3)
    return [replace_mongo_id(movie) for movie in top_movies]
