# MLChat — چت‌بات با پشتیبانی از مدل‌های `.pkl`

یک پروژهٔ Django با رابط چت که به کاربر اجازه می‌دهد با ارسال پیام متنی یا تصویر، از مدل‌های یادگیری ماشین ذخیره‌شده در فرمت `.pkl` پیش‌بینی بگیرد. ساختار طوری طراحی شده که مدل‌های جدید را بتوان بدون تغییرات عمده اضافه یا جایگزین کرد.

---

## فهرست مطالب
-  پیش‌نیازها
-  نصب و راه‌اندازی (لوکال)
-  راه‌اندازی Tesseract OCR (Windows / Ubuntu / macOS)
-  متغیرهای محیطی موردنیاز
-  اجرای برنامه
-  ساختار پروژه
-  نحوهٔ اضافه کردن مدل جدید
-  نکات مربوط به آپلود تصویر / OCR
-  پاک‌سازی تاریخچهٔ چت
-  لایسنس و منابع

---

## پیش‌نیازها
- Python 3.10+  
- pip  
- virtualenv (یا venv)  
- Git

فایل `requirements.txt` پروژه را بررسی کن و قبل از اجرا نصب کن:
```bash
python -m venv .venv
# windows
.venv\Scripts\activate
# linux / mac
source .venv/bin/activate

pip install -r requirements.txt
```

مثال پیشنهادی `requirements.txt` (پایه):
```
Django>=4.0
numpy
pandas
scikit-learn
pillow
pytesseract
deep-translator
requests
python-dotenv
```

---

##  نصب و راه‌اندازی (لوکال)
1. کد را کلون کن:
```bash
git clone <repo-url>
cd MLChat
```

2. محیط مجازی را فعال کن (همان‌طور که در بالا نشان داده شد) و وابستگی‌ها را نصب کن:
```bash
pip install -r requirements.txt
```

3. مایگریشن‌ها را اجرا کن (در صورت استفاده از session DB یا دیگر مدل‌ها):
```bash
python manage.py migrate
```

4. (اختیاری) یک سوپر یوزر بساز:
```bash
python manage.py createsuperuser
```

---

##  راه‌اندازی Tesseract OCR
برای پردازش تصویر (مدل دیابت)، پروژه از `pytesseract` و باینری `tesseract` استفاده می‌کند. — فقط دستورالعمل نصب را دنبال کنید.

### Windows
1. از یکی از buildهای رسمی یا UB Mannheim یک installer دانلود و نصب کن:  
   https://github.com/UB-Mannheim/tesseract/wiki
2. مسیر `tesseract.exe` معمولاً شبیه زیر است:
```
C:\Program Files\Tesseract-OCR\tesseract.exe
```
3. (پیشنهاد) متغیر محیطی `TESSERACT_CMD` را ست کن:
```powershell
setx TESSERACT_CMD "C:\Program Files\Tesseract-OCR\tesseract.exe"
```
4. اگر از Persian OCR استفاده می‌کنی، فایل `fas.traineddata` را در پوشهٔ `tessdata` نصب‌شده قرار بده:
```
C:\Program Files\Tesseract-OCR\tessdata\fas.traineddata
```

### Ubuntu / Debian
```bash
sudo apt-get update
sudo apt-get install -y tesseract-ocr tesseract-ocr-fas
```

### macOS (Homebrew)
```bash
brew install tesseract
# یا بسته‌های زبان اگر لازم است
```

### تست نصب
در محیطی که `tesseract` نصب شده:
```bash
tesseract --version
# یا از اسکریپت چک (اختیاری)
python utils/check_tesseract.py
```

**نکات خطاهای رایج**
- خطای `[WinError 740] The requested operation requires elevation`: معمولاً رخ می‌دهد اگر ویندوز نیاز به اجرای برنامه به‌صورت Administrator داشته باشد. راه‌حل‌ها:
  - در `Properties` فایل `tesseract.exe` بخش Compatibility مطمئن شو گزینه `Run as administrator` تیک نخورده.
  - مسیر باینری را در کد صریح ست کن تا از مسیر درست استفاده شود (نمونه زیر).
  - برای توسعهٔ موقت می‌توان runserver را از CMD باز شده با Run as Administrator اجرا کرد، اما **توصیه نشده** برای محیط production.

---

##  متغیرهای محیطی موردنیاز
بعضی مقادیر را باید به‌عنوان env var تنظیم کنید:

- `TESSERACT_CMD` — (اختیاری) مسیر `tesseract.exe`، مثال: `C:\Program Files\Tesseract-OCR\tesseract.exe`
- `TESSDATA_PREFIX` — (اختیاری) پوشهٔ `tessdata` که traineddata در آن قرار دارد.

مثال ست روی لینوکس / macOS:
```bash
export TESSERACT_CMD="/usr/bin/tesseract"
export TESSDATA_PREFIX="/usr/share/tesseract-ocr/4.00/tessdata/"
```

مثال ویندوز (PowerShell):
```powershell
setx TESSERACT_CMD "C:\Program Files\Tesseract-OCR\tesseract.exe"
```

---

##  اجرای برنامه (لوکال)
```bash
# محیط مجازی را فعال کن
python manage.py runserver
# سپس به http://127.0.0.1:8000/ برو
```

---

##  ساختار پروژه (موجود / پیشنهادی)
```
MLChat/
├── manage.py
├── MLChat/
│   ├── settings.py
│   └── urls.py
├── models/
│   ├── ml_handler.py            # مرکزی: MLModelHandler
│   ├── diabetes_prediction/
│   │   ├── diabetes_model.pkl
│   │   └── ml_model.py
│   └── movie_recommender/
│       ├── dict_mov.pkl
│       ├── model.pkl
│       ├── similarity.pkl
│       └── ml_model.py
├── chatbot/                     # django app
│   ├── views.py
│   ├── urls.py
│   └── forms.py
├──  templates/chat.html
├── static/
│       ├── css/
│           ├── style.css
│       └── js/
│           └── main.js
├── db.sqlite3
├── requirements.txt
├── README(PERSIAN).md
├── README(ENGLISH`).md
```

---

##  نحوهٔ اضافه کردن مدل جدید (الگوی سریع)
هر مدل باید رابطی مشابه داشته باشد تا `MLModelHandler` بتواند آن را صدا بزند. الگوی پیشنهادی:

**فایل: `models/<model_name>/ml_model.py`**
```python
import os
import pickle

class MyModel:
    REQUIRED_FIELDS = ['f1', 'f2']  # اگر فرم stepwise لازم است
    def __init__(self):
        base_dir = os.path.dirname(__file__)
        model_path = os.path.join(base_dir, 'model.pkl')
        with open(model_path, 'rb') as f:
            self.model = pickle.load(f)

    def predict(self, features: dict):
        # features: dict با کلیدهای REQUIRED_FIELDS یا شکل دلخواه
        # برگرداندن عدد یا هر خروجی‌ای که MLModelHandler منتظر است
        values = [float(features[f]) for f in self.REQUIRED_FIELDS]
        result = self.model.predict([values])
        return int(result[0])
```

**ثبت مدل در `models/ml_handler.py`**
فایل `MLModelHandler` فعلاً مدل‌ها را به‌صورت سخت‌کد لود می‌کند. برای اضافه کردن مدل جدید:
```python
from models.my_new_model.ml_model import MyModel

class MLModelHandler:
    def __init__(self):
        self.models = {
            'diabetes': DiabetesModel(),
            'movie': MovieRecommender(),
            'mynew': MyModel(),   # اضافه کردن این خط
        }
```

---

## ️ نکات مربوط به آپلود تصویر و OCR
- فرم آپلود (`DiabetesUploadForm`) از `ImageField` استفاده می‌کند. حتماً در فرم یا view محدودیت سایز و content-type قرار دهید:
```python
def clean_test_image(self):
    img = self.cleaned_data['test_image']
    if img.size > 5 * 1024 * 1024:
        raise forms.ValidationError("اندازهٔ تصویر نباید بیشتر از 5MB باشد.")
    if not img.content_type.startswith('image/'):
        raise forms.ValidationError("فایل آپلود شده باید تصویر باشد.")
    return img
```
- در `models/diabetes_prediction/ml_model.py` می‌توانید مسیر `tesseract` را از env بخوانید:
```python
import os, pytesseract
pytesseract.pytesseract.tesseract_cmd = os.environ.get('TESSERACT_CMD', r"C:\Users\Mehran\AppData\Local\Programs\Tesseract-OCR\tesseract.exe")
if os.environ.get('TESSDATA_PREFIX'):
    os.environ['TESSDATA_PREFIX'] = os.environ.get('TESSDATA_PREFIX')
```

---

##  پاک‌سازی تاریخچهٔ چت (Clear history)
تاریخچهٔ چت در `request.session['chat_history']` ذخیره می‌شود. برای پاکسازی می‌توانی endpoint ساده‌ای ایجاد کنی:

**views.py**
```python
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

@csrf_exempt
def clear_chat_history(request):
    if request.method == 'POST':
        request.session.pop('chat_history', None)
        request.session.pop('diabetes_state', None)
        request.session.modified = True
        return JsonResponse({'success': True})
    return JsonResponse({'success': False}, status=405)
```


---


##  لایسنس و منابع
- Tesseract OCR تحت Apache-2.0 است — لینک: https://github.com/tesseract-ocr/tesseract

