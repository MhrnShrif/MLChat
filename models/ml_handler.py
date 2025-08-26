from models.diabetes_prediction.ml_model import DiabetesModel
from models.movie_recommender.ml_model import MovieRecommender


class MLModelHandler:
    def __init__(self):
        self.models = {
            'diabetes': DiabetesModel(),
            'movie': MovieRecommender()
        }

    def predict(self, model_name, data):
        if model_name not in self.models:
            raise ValueError(f"Model '{model_name}' not found.")

        model = self.models[model_name]

        if model_name == 'diabetes':
            if 'image' in data and data['image'] is not None:
                try:
                    features = model.extract_features_from_image(data['image'])
                    missing = [f for f in DiabetesModel.REQUIRED_FIELDS if f not in features or features[f] == '']
                    if missing:
                        return {"type": "diabetes", "status": "incomplete", "missing_fields": missing, "source": "image", "features": features}
                    result = model.predict(features)
                    return {"type": "diabetes", "status": "success", "result": result, "source": "image", "features": features}
                except Exception as e:
                    return {"type": "diabetes", "status": "error", "message": f"خطا هنگام پردازش تصویر: {e}"}

            provided_keys = set(data.keys())
            required = set(DiabetesModel.REQUIRED_FIELDS)
            missing = [f for f in DiabetesModel.REQUIRED_FIELDS if f not in data or data.get(f) in [None, ""]]
            if not missing and required.issubset(provided_keys):
                try:
                    result = model.predict(data)
                    return {"type": "diabetes", "status": "success", "result": result, "source": "form"}
                except Exception as e:
                    return {"type": "diabetes", "status": "error", "message": f"خطا هنگام پیش‌بینی: {e}"}
            else:
                return {"type": "diabetes", "status": "incomplete", "missing_fields": missing}

        elif model_name == 'movie':
            title_or_genre = data.get('title', '').strip()
            if not title_or_genre:
                return {"type": "movie", "status": "error", "message": "لطفاً نام فیلم یا ژانر را وارد کنید"}

            try:
                titles, posters_or_options = model.recommend(title_or_genre)
            except Exception as e:
                return {"type": "movie", "status": "error", "message": f"خطا در سیستم پیشنهاددهی: {e}"}

            # titles == None  => need confirmation/options
            if titles is None:
                return {
                    "type": "movie",
                    "status": "need_confirmation",
                    "options": posters_or_options,
                    "message": "کدام یک از این فیلم‌ها مد نظر شماست؟"
                }
            elif not titles:
                return {
                    "type": "movie",
                    "status": "error",
                    "message": "متأسفانه فیلمی با این عنوان یا ژانر پیدا نشد. لطفاً چیز دیگری امتحان کنید."
                }
            else:
                return {
                    "type": "movie",
                    "status": "success",
                    "titles": titles,
                    "posters": posters_or_options,
                    "message": f"نتایج پیشنهادی برای '{title_or_genre}':"
                }
