import requests
import random
import pickle
import nltk
from nltk.stem import PorterStemmer
ps = PorterStemmer()
from django.conf import settings 
import numpy as np 
import pandas as pd 
from django.shortcuts import render
from users.models import UserList, ListItem
from .recommender import (
    recommend_dynamic, convert_api_data, convert_cast_api_data,
    remove_space, fetch_director_api_data, stems
)

API_KEY = settings.TMDB_API_KEY 
movies_kaggle_csv = pickle.load(open("nbs/artifacts/movie_list.pkl", "rb"))

def landing_page(request):
    category = request.GET.get("category", "popular")
    search_query = request.GET.get("search", "")
    page = int(request.GET.get("page", 1))
    next_page = page + 1
    base_url = "https://api.themoviedb.org/3/movie/"
    error_message = ""
    user_lists = UserList.objects.filter(user=request.user) if request.user.is_authenticated else None

    if search_query:
        url = f"https://api.themoviedb.org/3/search/movie?api_key={API_KEY}&query={search_query}&page={page}"
    else:
        url = f"{base_url}{category}?api_key={API_KEY}&page={page}"

    try:
        resp = requests.get(url)
        resp.raise_for_status()
        data = resp.json().get("results", [])
        total_pages = resp.json().get("total_pages", 1)
        has_next = page < total_pages
    except Exception:
        data, has_next = [], False
        error_message = "Something went wrong"

    if request.headers.get("HX-Request"):
        return render(request, "movies/partials/_movie_list.html", {"movies": data,
        "category": category,
        "search_query": search_query,
        "error_message": error_message,
        "next_page": next_page,
        "has_next": has_next,
        "user_lists": user_lists})
    return render(request, "movies/landing.html", {
        "movies": data,
        "category": category,
        "search_query": search_query,
        "error_message": error_message,
        "next_page": next_page,
        "has_next": has_next,
        "user_lists": user_lists
    })

def movie_detail(request, movie_id):
    urls = {
        "detail": f"https://api.themoviedb.org/3/movie/{movie_id}?api_key={API_KEY}",
        "credits": f"https://api.themoviedb.org/3/movie/{movie_id}/credits?api_key={API_KEY}",
        "keywords": f"https://api.themoviedb.org/3/movie/{movie_id}/keywords?api_key={API_KEY}"
    }
    user_lists = UserList.objects.filter(user=request.user) if request.user.is_authenticated else None
    error_message = ""
    new_api_df = pd.DataFrame()

    try:
        movie = requests.get(urls["detail"]).json()
        credits = requests.get(urls["credits"]).json()
        keywords = requests.get(urls["keywords"]).json()

        api_df = pd.DataFrame([movie])\
            .merge(pd.DataFrame([credits]), on="id")\
            .merge(pd.DataFrame([keywords]), on="id")

        api_df = api_df[["id", "title", "overview", "genres", "keywords", "cast", "crew"]]
        api_df["genres"] = api_df["genres"].apply(convert_api_data)
        api_df["keywords"] = api_df["keywords"].apply(convert_api_data)
        api_df["cast"] = api_df["cast"].apply(convert_cast_api_data)
        api_df["crew"] = api_df["crew"].apply(fetch_director_api_data)
        api_df["overview"] = api_df["overview"].apply(lambda x: x.split())
        for col in ["cast", "crew", "genres", "keywords"]:
            api_df[col] = api_df[col].apply(remove_space)

        api_df["tags"] = api_df["overview"] + api_df["genres"] + api_df["keywords"] + api_df["cast"] + api_df["crew"]
        new_api_df = api_df[["id", "title", "tags"]]
        new_api_df["tags"] = new_api_df["tags"].apply(lambda x: " ".join(x).lower())
        new_api_df["tags"] = new_api_df["tags"].apply(stems)

        titles, posters, data = recommend_dynamic(new_api_df)
    except Exception as e:
        titles, posters, data = [], [], []
        error_message = "Movie processing or recommendation failed."

    zipped_recs = zip(titles, posters, data)

    return render(request, "movies/movie_detail.html", {
        "movie": movie if 'movie' in locals() else {},
        "new_api_df": new_api_df,
        "error_message": error_message,
        "credits": credits if 'credits' in locals() else {},
        "keywords": keywords if 'keywords' in locals() else {},
        "user_lists": user_lists,
        "zipped_recommendations": zipped_recs
    })

def user_based_recommendation(request):
    user_lists = UserList.objects.filter(user=request.user) if request.user.is_authenticated else None

    if request.user.is_authenticated:
        items = ListItem.objects.filter(list__in=user_lists)
        movies_data = []
        for item in items:
            resp = requests.get(
                f"https://api.themoviedb.org/3/movie/{item.movie_id}?api_key={API_KEY}&append_to_response=credits,keywords"
            )
            if resp.status_code == 200:
                movies_data.append(resp.json())

        if not movies_data:
            return render(request, "movies/partials/_recommended_movies.html", {
                "zipped_recommendations": [],
                "user_lists": user_lists
            })

        df = pd.DataFrame(movies_data)
        df["cast"] = df["credits"].apply(lambda c: c["cast"])
        df["crew"] = df["credits"].apply(lambda c: c["crew"])
        df["keywords"] = df["keywords"].apply(lambda k: k["keywords"])
        df = df[["id", "title", "overview", "genres", "keywords", "cast", "crew"]]

        df["genres"] = df["genres"].apply(convert_api_data)
        df["keywords"] = df["keywords"].apply(convert_api_data)
        df["cast"] = df["cast"].apply(convert_cast_api_data)
        df["crew"] = df["crew"].apply(fetch_director_api_data)
        df["overview"] = df["overview"].apply(lambda x: x.split() if isinstance(x, str) else [])
        for col in ["cast", "crew", "genres", "keywords"]:
            df[col] = df[col].apply(remove_space)

        df["tags"] = df["overview"] + df["genres"] + df["keywords"] + df["cast"] + df["crew"]
        df["tags"] = df["tags"].apply(lambda x: " ".join(x).lower())
        df["tags"] = df["tags"].apply(stems)

        selected_title = df["title"].sample(1).iloc[0]
        titles, posters, data = recommend_dynamic(df[df["title"] == selected_title])
        recs = list(zip(titles, posters, data))
        recs = random.sample(recs, 5) if len(recs) >= 5 else recs

        context = {"zipped_recommendations": recs, "user_lists": user_lists}
    else:
        resp = requests.get(f"https://api.themoviedb.org/3/movie/popular?api_key={API_KEY}")
        results = resp.json().get("results", [])[:5]
        recs = [
            (m["title"], f"https://image.tmdb.org/t/p/w500{m['poster_path']}", m)
            for m in results
        ]
        context = {"zipped_recommendations": recs, "user_lists": []}

    template = "movies/partials/_recommended_movies.html" if request.headers.get("HX-Request") else "includes/reccommend_home.html"
    return render(request, template, context)
