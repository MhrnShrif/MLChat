import os
import pickle
import pandas as pd
import requests
from difflib import get_close_matches
from deep_translator import GoogleTranslator
import re

class MovieRecommender:
    def __init__(self):
        self.fa_to_en = {
            "اکشن": "action",
            "کمدی": "comedy",
            "درام": "drama",
            "ترسناک": "horror",
            "علمی تخیلی": "sci-fi",
            "علمی": "sci-fi",
            "تخیلی": "sci-fi",
            "ماجراجویی": "adventure",
            "انیمیشن": "animation",
            "رمانتیک": "romance",
            "عاشقانه": "romance",
            "جنایی": "crime",
            "تاریخی": "history",
            "جنگی": "war",
            "موزیکال": "musical",
            "اسپورت": "sport",
        }

        base_dir = os.path.dirname(__file__)
        dict_path = os.path.join(base_dir, 'dict_mov.pkl')
        sim_path = os.path.join(base_dir, 'similarity.pkl')

        if not os.path.exists(dict_path) or not os.path.exists(sim_path):
            raise FileNotFoundError("اطمینان حاصل کنید dict_mov.pkl و similarity.pkl در پوشه models/movie_recommender وجود دارند.")

        with open(dict_path, 'rb') as f:
            self.movies_dict = pickle.load(f)
        self.movies = pd.DataFrame(self.movies_dict).reset_index(drop=True)

        with open(sim_path, 'rb') as f:
            self.similarity = pickle.load(f)

        try:
            self.translator_fa_to_en = GoogleTranslator(source="fa", target="en")
            self.translator_en_to_fa = GoogleTranslator(source="en", target="fa")
        except Exception as e:
            print("Translator init failed:", e)
            self.translator_fa_to_en = None
            self.translator_en_to_fa = None

        self.tmdb_api_key = os.environ.get('TMDB_API_KEY')
        if not self.tmdb_api_key:
            print("Warning: TMDB_API_KEY not found in environment. Poster fetching will return placeholders.")
            self.tmdb_api_key = None

        if 'title' in self.movies.columns:
            self._titles_lower = [str(t).lower() for t in self.movies['title'].tolist()]
        else:
            self._titles_lower = []

    def normalize_input(self, text: str) -> str:
        if not text:
            return text
        text = text.strip()
        if text in self.fa_to_en:
            return self.fa_to_en[text]
        return text

    def _map_fa_keywords(self, text: str) -> str:
        if not text:
            return text
        lowered = text.lower()
        mapped = []
        for fa, en in self.fa_to_en.items():
            if fa in lowered:
                mapped.append(en)
        if mapped:
            return mapped[0]
        return text

    def translate_to_en(self, text: str) -> str:
        if not text:
            return text
        local_mapped = self._map_fa_keywords(text)
        if local_mapped != text:
            return local_mapped

        if self.translator_fa_to_en:
            try:
                translated = self.translator_fa_to_en.translate(text)
                return translated
            except Exception as e:
                print("translate_to_en failed:", e)
                return text
        # fallback to original text
        return text

    def translate_to_fa(self, text: str) -> str:
        if not text:
            return text
        if self.translator_en_to_fa:
            try:
                return self.translator_en_to_fa.translate(text)
            except Exception as e:
                print("translate_to_fa failed:", e)
                return text
        return text

    def fetch_poster(self, movie_id: int) -> str:
        if not self.tmdb_api_key:
            return "https://via.placeholder.com/300x450.png?text=No+Image+Key"

        url = f"https://api.themoviedb.org/3/movie/{movie_id}"
        params = {'api_key': self.tmdb_api_key, 'language': 'en-US'}
        try:
            res = requests.get(url, params=params, timeout=5)
            res.raise_for_status()
            data = res.json()
            poster_path = data.get('poster_path')
            if poster_path:
                return f"https://image.tmdb.org/t/p/w500/{poster_path}"
        except Exception as e:
            print(f"Error fetching poster for movie_id {movie_id}: {e}")
        return "https://via.placeholder.com/300x450.png?text=No+Image"

    def is_persian(self, text: str) -> bool:
        return bool(re.search(r'[\u0600-\u06FF]', str(text)))

    def recommend(self, query: str):
        if not query:
            return [], []

        user_used_farsi = self.is_persian(query)

        query = self.normalize_input(query)
        if user_used_farsi:
            mapped = self._map_fa_keywords(query)
            if mapped != query:
                query_en = mapped.lower()
            else:
                query_en = self.translate_to_en(query).lower()
        else:
            query_en = query.lower()

        if 'tags' in self.movies.columns:
            try:
                genre_matches = self.movies[self.movies['tags'].str.contains(query_en, case=False, na=False)]
                if len(genre_matches) > 0:
                    recommended = genre_matches.head(5)
                    recommended_titles = recommended['title'].tolist()
                    recommended_posters = [self.fetch_poster(mid) for mid in recommended['id'].tolist()]
                    if user_used_farsi:
                        recommended_titles = [self.translate_to_fa(t) for t in recommended_titles]
                    return recommended_titles, recommended_posters
            except Exception as e:
                print("genre search failed:", e)

        if 'title' not in self.movies.columns:
            return [], []

        try:
            matching_titles = self.movies[self.movies['title'].str.contains(query_en, case=False, na=False)]
        except Exception:
            matching_titles = pd.DataFrame()

        if len(matching_titles) == 0:
            all_titles = self._titles_lower
            q = query_en.lower()
            close = get_close_matches(q, all_titles, n=5, cutoff=0.4)
            if close:
                idxs = []
                for c in close:
                    try:
                        idx = self._titles_lower.index(c)
                        idxs.append(idx)
                    except ValueError:
                        continue
                options = [self.movies.iloc[i]['title'] for i in idxs]
                if user_used_farsi:
                    options = [self.translate_to_fa(t) for t in options]
                return None, options
            else:
                return [], []

        if len(matching_titles) > 1:
            titles = matching_titles['title'].tolist()[:5]
            if user_used_farsi:
                titles = [self.translate_to_fa(t) for t in titles]
            return None, titles

        matched_title = matching_titles.iloc[0]['title']
        try:
            movie_pos = int(matching_titles.index[0])
            if hasattr(self, 'similarity') and len(self.similarity) == len(self.movies):
                distances = self.similarity[movie_pos]
            else:
                print("similarity dimension mismatch; cannot compute similar movies.")
                return [], []
        except Exception as e:
            print("Error locating movie position in similarity matrix:", e)
            return [], []

        movies_list = sorted(list(enumerate(distances)), reverse=True, key=lambda x: x[1])[1:6]

        recommended_titles = []
        recommended_posters = []
        for idx, score in movies_list:
            try:
                movie_id = int(self.movies.iloc[idx]['id'])
                title = self.movies.iloc[idx]['title']
            except Exception:
                continue
            if user_used_farsi:
                title = self.translate_to_fa(title)
            recommended_titles.append(title)
            recommended_posters.append(self.fetch_poster(movie_id))

        return recommended_titles, recommended_posters

    def get_all_titles(self):
        if 'title' in self.movies.columns:
            return self.movies['title'].tolist()
        return []
