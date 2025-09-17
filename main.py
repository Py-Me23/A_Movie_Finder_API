from fastapi import FastAPI, HTTPException, status
from db import movies_collection, user_collection
from pydantic import BaseModel, Field, EmailStr
from utils import replace_mongo_id
from passlib.context import CryptContext
import requests
import os
from dotenv import load_dotenv
from hash_password import verify_password, get_password_hash
from tokens import create_access_token, UserInfo

load_dotenv()

app = FastAPI()

OMDB_API_URL = os.getenv("OMDB_API_URL")
OMDB_API_KEY = os.getenv("OMDB_API_KEY")


class UserRegisteration(BaseModel):
    name: str = Field(min_length=2, max_length=50)
    email: EmailStr
    password: str = Field(min_length=8)


class UserLogin(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)


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
    # Check OMDb API to ensure movie exists
    if not OMDB_API_URL or not OMDB_API_KEY:
        raise HTTPException(status_code=500, detail="OMDb API credentials missing")

    # Prefer to check by imdb_ID if provided, else by title
    query_params = {"i": movie.imdb_ID, "apikey": OMDB_API_KEY}  # by IMDb ID
    response = requests.get(OMDB_API_URL, params=query_params)

    if response.status_code != 200:
        raise HTTPException(status_code=500, detail="Error fetching data from OMDb API")

    omdb_data = response.json()

    if omdb_data.get("Response") == "False":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Movie '{movie.title}' does not exist in OMDb. Cannot add to favorites.",
        )

    # Optionally verify title/year match OMDb result to prevent mismatches
    if movie.title.lower() != omdb_data.get("Title", "").lower():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Title mismatch. Please provide the exact title from OMDb.",
        )

    # Insert only if valid
    movies_collection.insert_one(movie.model_dump())
    return {"message": f"'{movie.title}' added successfully to favorites."}


@app.get("/favorites")
def list_favorites():
    movies = list(movies_collection.find())
    return [replace_mongo_id(movie) for movie in movies]


@app.get("/favorites/top-3")
def top_3_favorites():
    top_movies = movies_collection.find().sort("user_rating", -1).limit(3)
    return [replace_mongo_id(movie) for movie in top_movies]


# <=========user Registeration==========>


@app.post("/Signup", tags=["USERS👨"])
def register_user(user: UserRegisteration):
    # check if user exists
    user_exists = user_collection.find_one(filter={"email": user.email})
    if user_exists:
        return {"error": "Email alreadly exists!"}

    # hash the password
    hashed_password = get_password_hash(user.password)

    # create user
    new_user = user_collection.insert_one(
        {
            "name": user.name,
            "email": user.email,
            "password": hashed_password,
        }
    )
    return {"message": "User registered successfully"}


# <=============user login========>
@app.post("/Signin")
def login_user(user: UserLogin):
    # check if user exist in database
    user_in_db = user_collection.find_one(filter={"email": user.email})
    if not user_in_db:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "inavlid email!")

    # compare and verify user password
    valid_password = verify_password(user.password, user_in_db["password"])
    if not valid_password:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid password!")

    # create access token for user
    user_data = UserInfo(
        id=str(user_in_db["_id"]), email=user_in_db["email"], name=user_in_db["name"]
    )
    token = create_access_token(user_data)

    # return success message
    return {
        "message": "Login successfully",
        "data": {"tokens": token},
    }
