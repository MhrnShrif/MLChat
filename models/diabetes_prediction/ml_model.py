import os
import pickle
import numpy as np
import warnings
import re
from PIL import Image
import pytesseract
from sklearn.exceptions import InconsistentVersionWarning

warnings.filterwarnings("ignore", category=InconsistentVersionWarning)
pytesseract.pytesseract.tesseract_cmd = r"C:\Users\Mehran\AppData\Local\Programs\Tesseract-OCR\tesseract.exe"


class DiabetesModel:
    REQUIRED_FIELDS = [
        'Pregnancies', 'Glucose', 'BloodPressure', 'SkinThickness',
        'Insulin', 'BMI', 'DiabetesPedigreeFunction', 'Age'
    ]

    KEYWORDS = {
        'Pregnancies': ['pregnancies', 'بارداری'],
        'Glucose': ['glucose', 'قند'],
        'BloodPressure': ['bloodpressure', 'bp', 'فشار خون'],
        'SkinThickness': ['skinthickness', 'پوست', 'skin thickness'],
        'Insulin': ['insulin', 'انسولین'],
        'BMI': ['bmi', 'body mass index', 'شاخص توده بدنی'],
        'DiabetesPedigreeFunction': ['diabetespedigreefunction', 'diabetes pedigree', 'دیابت'],
        'Age': ['age', 'سن']
    }

    FIELD_DESCRIPTIONS = {
        'Pregnancies': 'تعداد دفعات بارداری',
        'Glucose': 'غلظت گلوکز پلاسما در تست تحمل گلوکز خوراکی',
        'BloodPressure': 'فشار خون دیاستولیک (mm Hg)',
        'SkinThickness': 'ضخامت چین پوستی تریسپس (mm)',
        'Insulin': 'انسولین سرم 2 ساعت (mu U/ml)',
        'BMI': 'شاخص توده بدنی (وزن بر حسب کیلوگرم تقسیم بر مجذور قد بر حسب متر)',
        'DiabetesPedigreeFunction': 'تابع تبار دیابت',
        'Age': 'سن (سال)'
    }

    def __init__(self):
        base_dir = os.path.dirname(__file__)
        model_path = os.path.join(base_dir, 'diabetes_model.pkl')
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"Model file not found at {model_path}")
        with open(model_path, 'rb') as f:
            self.model = pickle.load(f)

    @staticmethod
    def _persian_to_english_digits(s: str) -> str:
        if not isinstance(s, str):
            return s
        persian_digits = '۰۱۲۳۴۵۶۷۸۹'
        english_digits = '0123456789'
        for p, e in zip(persian_digits, english_digits):
            s = s.replace(p, e)
        return s

    @staticmethod
    def _safe_cast_int(value, default=0):
        if value is None or value == '':
            return default
        try:
            if isinstance(value, str):
                value = DiabetesModel._persian_to_english_digits(value.strip())
            return int(float(value))
        except Exception:
            raise ValueError(f"قابل تبدیل به عدد صحیح نیست: {value}")

    @staticmethod
    def _safe_cast_float(value, default=0.0):
        if value is None or value == '':
            return default
        try:
            if isinstance(value, str):
                value = DiabetesModel._persian_to_english_digits(value.strip())
                value = value.replace(',', '.')
            return float(value)
        except Exception:
            raise ValueError(f"قابل تبدیل به عدد اعشاری نیست: {value}")

    def predict(self, features: dict):
        try:
            values = np.array([[ 
                self._safe_cast_int(features.get('Pregnancies', 0)),
                self._safe_cast_int(features.get('Glucose', 0)),
                self._safe_cast_int(features.get('BloodPressure', 0)),
                self._safe_cast_int(features.get('SkinThickness', 0)),
                self._safe_cast_int(features.get('Insulin', 0)),
                self._safe_cast_float(features.get('BMI', 0.0)),
                self._safe_cast_float(features.get('DiabetesPedigreeFunction', 0.0)),
                self._safe_cast_int(features.get('Age', 0))
            ]])
        except ValueError as e:
            raise

        prediction = self.model.predict(values)
        return int(prediction[0])

    def extract_features_from_image(self, uploaded_file):
        try:
            image = Image.open(uploaded_file)
        except Exception as e:
            raise ValueError(f"خطا در باز کردن فایل تصویر: {e}")
        try:
            text = pytesseract.image_to_string(image, lang='eng+fas')
        except Exception as e:
            raise RuntimeError(f"خطا در OCR (اطمینان حاصل کنید tesseract و پکیج‌های زبان نصب شده‌اند): {e}")

        text = text.replace('،', ',').replace(':', ' ').lower()
        text = self._persian_to_english_digits(text)

        features = {}
        for field, keys in self.KEYWORDS.items():
            found = False
            for key in keys:
                pattern = rf"{re.escape(key)}[\s:\-]*([\d\.,]+)"
                match = re.search(pattern, text, flags=re.IGNORECASE)
                if match:
                    raw_val = match.group(1).strip()
                    raw_val = raw_val.replace(',', '.')
                    raw_val = self._persian_to_english_digits(raw_val)
                    features[field] = raw_val
                    found = True
                    break
            if not found:
                pass
        print("OCR OUTPUT >>>")
        print(text)
        print("<<< OCR END")

        return features

    def get_field_description(self, field_name):
        return self.FIELD_DESCRIPTIONS.get(field_name, field_name)
