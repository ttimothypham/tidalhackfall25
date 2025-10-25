from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import requests, os
from dotenv import load_dotenv
from data_cleaning import clean_and_filter_data
from model import recommend_recipes

app = FastAPI()

@app.get("/")
def read_root():
    return {"message": "Hello from FoodBank API!"}

@app.get("/recipes")
def get_recipes(ingredient: str = Query(...)):
    url = "https://api.spoonacular.com/recipes/findByIngredients"
    params = {"ingredients": ingredient, "number": 10, "apiKey": API_KEY}
    res = requests.get(url, params=params)
    data = res.json()

    # Clean and filter
    //filtered = clean_and_filter_data(data)

    # Recommend (ML logic)
    recommendations = recommend_recipes(filtered)

    return {"recipes": recommendations}