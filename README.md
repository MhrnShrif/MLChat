MLChat — Chatbot with support for .pkl models
A Django project with a chat interface that allows users to submit text messages or images and receive predictions from machine learning models stored as .pkl files. The structure is designed so new models can be added or replaced without major changes.

Table of contents
Prerequisites
Local installation and setup
Tesseract OCR setup (Windows / Ubuntu / macOS)
Required environment variables
Running the application
Project structure
How to add a new model
Notes about image upload / OCR
Clearing chat history
License and references
Prerequisites
Python 3.10+
pip
virtualenv (or venv)
Git
Check the project's requirements.txt and install dependencies before running:

python -m venv .venv
# windows
.venv\Scripts\activate
# linux / mac
source .venv/bin/activate

pip install -r requirements.txt
Example requirements.txt (base):

Django>=4.0
numpy
pandas
scikit-learn
pillow
pytesseract
deep-translator
requests
python-dotenv
Local installation and setup
Clone the repository:
git clone <repo-url>
cd MLChat
Activate the virtual environment (as shown above) and install dependencies:
pip install -r requirements.txt
Run migrations (if sessions or other models are used):
python manage.py migrate
(Optional) Create a superuser:
python manage.py createsuperuser
Tesseract OCR setup
For image processing (diabetes model), the project uses pytesseract and the tesseract binary. Follow the installation instructions below.

Windows
Download and install a build (for example UB Mannheim): https://github.com/UB-Mannheim/tesseract/wiki
The tesseract.exe path is typically:
C:\Program Files\Tesseract-OCR\tesseract.exe
(Recommended) Set the TESSERACT_CMD environment variable:
setx TESSERACT_CMD "C:\Program Files\Tesseract-OCR\tesseract.exe"
If you use Persian OCR, place fas.traineddata in the installed tessdata folder:
C:\Program Files\Tesseract-OCR\tessdata\fas.traineddata
Ubuntu / Debian
sudo apt-get update
sudo apt-get install -y tesseract-ocr tesseract-ocr-fas
macOS (Homebrew)
brew install tesseract
# or install language packages if needed
Test the installation
In an environment where tesseract is installed:

tesseract --version
# or use the optional check script
python utils/check_tesseract.py
Common issues

Error [WinError 740] The requested operation requires elevation: this usually occurs if Windows requires running the program as Administrator. Solutions:
In the Properties of tesseract.exe, make sure the Compatibility option "Run this program as administrator" is unchecked.
Set the explicit tesseract binary path in code to ensure the correct executable is used (example below).
For temporary development testing, you can run the Django dev server from a CMD opened as Administrator, but this is not recommended for production.
Required environment variables
Set the following environment variables as needed:

TESSERACT_CMD — (optional) path to the tesseract executable, e.g. C:\Program Files\Tesseract-OCR\tesseract.exe
TESSDATA_PREFIX — (optional) path to the tessdata folder containing traineddata files
Example for Linux / macOS:

export TESSERACT_CMD="/usr/bin/tesseract"
export TESSDATA_PREFIX="/usr/share/tesseract-ocr/4.00/tessdata/"
Example for Windows (PowerShell):

setx TESSERACT_CMD "C:\Program Files\Tesseract-OCR\tesseract.exe"
Running the application (local)
# activate virtualenv
python manage.py runserver
# then open http://127.0.0.1:8000/
Project structure (current / recommended)
MLChat/
├── manage.py
├── MLChat/
│   ├── settings.py
│   └── urls.py
├── models/
│   ├── ml_handler.py            # central: MLModelHandler
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
├── templates/
│   └── chat.html
├── static/
│   ├── css/
│   │   └── style.css
│   └── js/
│       └── main.js
├── db.sqlite3
├── requirements.txt
├── README(ENGLISH).md
├── README(PERSIAN).md
How to add a new model (quick template)
Each model should implement a similar interface so MLModelHandler can call it. Suggested template:

File: models/<model_name>/ml_model.py

import os
import pickle

class MyModel:
    REQUIRED_FIELDS = ['f1', 'f2']  # if stepwise form is required
    def __init__(self):
        base_dir = os.path.dirname(__file__)
        model_path = os.path.join(base_dir, 'model.pkl')
        with open(model_path, 'rb') as f:
            self.model = pickle.load(f)

    def predict(self, features: dict):
        # features: dict with keys matching REQUIRED_FIELDS or other format
        # Return the output expected by MLModelHandler (e.g. int label)
        values = [float(features[f]) for f in self.REQUIRED_FIELDS]
        result = self.model.predict([values])
        return int(result[0])
Register the model in models/ml_handler.py The current MLModelHandler loads models statically. To add a new model:

from models.my_new_model.ml_model import MyModel

class MLModelHandler:
    def __init__(self):
        self.models = {
            'diabetes': DiabetesModel(),
            'movie': MovieRecommender(),
            'mynew': MyModel(),   # add this line
        }
Notes about image upload / OCR
The upload form (DiabetesUploadForm) uses an ImageField. Validate file size and content-type in the form or view:
def clean_test_image(self):
    img = self.cleaned_data['test_image']
    if img.size > 5 * 1024 * 1024:
        raise forms.ValidationError("Image size must not exceed 5MB.")
    if not img.content_type.startswith('image/'):
        raise forms.ValidationError("Uploaded file must be an image.")
    return img
In models/diabetes_prediction/ml_model.py you can read the tesseract path from env:
import os, pytesseract
pytesseract.pytesseract.tesseract_cmd = os.environ.get('TESSERACT_CMD', r"C:\Users\Mehran\AppData\Local\Programs\Tesseract-OCR\tesseract.exe")
if os.environ.get('TESSDATA_PREFIX'):
    os.environ['TESSDATA_PREFIX'] = os.environ.get('TESSDATA_PREFIX')
Clearing chat history (Clear history)
Chat history is stored in request.session['chat_history']. To clear it, add a simple endpoint:

views.py

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
License and references
Tesseract OCR is available under the Apache-2.0 license — https://github.com/tesseract-ocr/tesseract
