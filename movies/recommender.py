
import nltk #relate similar words
import pandas as pd
import pickle
import requests
from nltk.stem import PorterStemmer
ps = PorterStemmer()
from sklearn.feature_extraction.text import CountVectorizer #to create vector
cv = CountVectorizer(max_features=5000, stop_words= 'english')
from sklearn.metrics.pairwise import cosine_similarity #getting similar vectors
from django.conf import settings 


API_KEY = settings.TMDB_API_KEY 
movies_kaggle_csv = pickle.load(open("nbs/artifacts/movie_list.pkl", 'rb'))
similarity = pickle.load(open("nbs/artifacts/similarity.pkl", 'rb'))


def convert_api_data(text): #converts string to list 
    return [g['name'] for g in text]

def convert_cast_api_data(text): #converts string to list 
    l = []
    counter = 0
    for i in text:
        if counter < 3:
            l.append(i['name'])
        counter+= 1
    return l

def remove_space(words):
    l = []
    for i in words:
        l.append(i.replace(" ", ""))
    return l

def fetch_director_api_data(text): 
    l = []
    for i in (text):
        if i['job'] == 'Director':
            l.append(i['name'])
            break
    return l

#checking words by turning paragrapgh into list of words to stem and then turning into paragraph again 
def stems(text):
    l = []
    for i in text.split():
        l.append(ps.stem(i)) #after performing stem append to list
    
    return " ".join(l)


def fetch_poster(movie_id):
    url = "https://api.themoviedb.org/3/movie/{}?api_key=8265bd1679663a7ea12ac168da84d2e8&language=en-US".format(movie_id)
    data = requests.get(url)
    data = data.json()
    poster_path = data['poster_path']
    full_path = "https://image.tmdb.org/t/p/w500/" + poster_path
    return full_path
def recommend_dynamic(api_movie_df):
    new_movie = api_movie_df.iloc[0]

    new_movie_df = pd.DataFrame([{
        'movie_id': new_movie['id'],  # Ensure 'movie_id' matches the static dataset
        'title': new_movie['title'],
        'tags': new_movie['tags']
    }])

    combined_df = pd.concat([movies_kaggle_csv, new_movie_df], ignore_index=True)
    vectors = cv.fit_transform(combined_df['tags']).toarray()
    similarity = cosine_similarity(vectors)

    movie_index = len(combined_df) - 1
    distances = sorted(list(enumerate(similarity[movie_index])), reverse=True, key=lambda x: x[1])[1:6]

    recommended_names = []
    recommended_posters = []
    recommended_data = []
    recommended_trailers = []


    for i in distances:
        movie = combined_df.iloc[i[0]]
        movie_id = movie.get('movie_id') or movie.get('id')  # Safe fallback
        movie_title = movie.get('title', 'Unknown Title')
        recommended_names.append(movie_title)
        recommended_posters.append(fetch_poster(movie_id))
        recommended_data.append(get_api_recommended_data(movie_id))
        
    return recommended_names, recommended_posters, recommended_data



def get_api_recommended_data(movie_id):
    error_message = "" 
    url = f"https://api.themoviedb.org/3/movie/{movie_id}?api_key={API_KEY}"
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.json()  # ✅ Return just the movie dict
    except Exception as e:
        print("Failed to fetch movie details:", e)
        return {}  # Return empty dict on error


def get_api_recomended_video(movie_id):
    error_message = "" 
    url = f"https://api.themoviedb.org/3/movie/550/videos?api_key={API_KEY}"
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.json()  # ✅ Return just the movie dict
    except Exception as e:
        print("Failed to fetch movie details:", e)
        return {}  # Return empty dict on error
    

