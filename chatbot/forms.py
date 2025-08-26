from django import forms

MODEL_CHOICES = [
    ('diabetes', 'پیشبینی دیابت'),
    ('movie', 'پیشنهاد فیلم'),
]


class ModelSelectForm(forms.Form):
    model = forms.ChoiceField(choices=MODEL_CHOICES, label='انتخاب مدل', widget=forms.Select(attrs={
        'class': 'bg-white/20 text-white rounded-lg px-3 py-1 text-sm border border-white/30 focus:outline-none focus:ring-2 focus:ring-white/50',
        'onchange': 'this.form.submit()'
    }))


class DiabetesStepForm(forms.Form):
    Pregnancies = forms.IntegerField(label='تعداد بارداری‌ها', widget=forms.NumberInput(attrs={'placeholder': 'مثال: 2'}))
    Glucose = forms.IntegerField(label='قند خون (mg/dL)', widget=forms.NumberInput(attrs={'placeholder': 'مثال: 120'}))
    BloodPressure = forms.IntegerField(label='فشار خون (mmHg)', widget=forms.NumberInput(attrs={'placeholder': 'مثال: 70'}))
    SkinThickness = forms.IntegerField(label='ضخامت پوست (mm)', widget=forms.NumberInput(attrs={'placeholder': 'مثال: 20'}))
    Insulin = forms.IntegerField(label='انسولین', widget=forms.NumberInput(attrs={'placeholder': 'مثال: 85'}))
    BMI = forms.FloatField(label='شاخص توده بدنی (BMI)', widget=forms.NumberInput(attrs={'placeholder': 'مثال: 28.5'}))
    DiabetesPedigreeFunction = forms.FloatField(label='Diabetes Pedigree Function', widget=forms.NumberInput(attrs={'placeholder': 'مثال: 0.5'}))
    Age = forms.IntegerField(label='سن', widget=forms.NumberInput(attrs={'placeholder': 'مثال: 33'}))

class DiabetesUploadForm(forms.Form):
    test_image = forms.ImageField(label='آپلود عکس آزمایش')

class MovieForm(forms.Form):
    title = forms.CharField(label='Movie Title', widget=forms.TextInput(attrs={'placeholder': 'مثال: فیلم عاشقانه'}))
