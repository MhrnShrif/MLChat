from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
import json
from models.ml_handler import MLModelHandler
from models.diabetes_prediction.ml_model import DiabetesModel
from .forms import *

handler = MLModelHandler()


def append_message(chat_history, sender, message):
    if not message:
        return
    last = chat_history[-1] if chat_history else None
    candidate = (sender, message)
    if last == candidate:
        return
    chat_history.append(candidate)


def to_english_digits(s: str) -> str:
    if not isinstance(s, str):
        return s
    persian = '۰۱۲۳۴۵۶۷۸۹'
    english = '0123456789'
    for p, e in zip(persian, english):
        s = s.replace(p, e)
    return s.strip()


def process_user_post(request, chat_history, diabetes_state, selected_model):
    context_updates = {}

    is_user_input_present = bool(request.POST.get('user_input', '').strip())
    is_file_present = 'test_image' in request.FILES and request.FILES.get('test_image') is not None

    if 'model' in request.POST and not is_user_input_present and not is_file_present:
        selected_model = request.POST.get('model')
        request.session['selected_model'] = selected_model

        if selected_model == 'diabetes':
            append_message(chat_history, 'bot', 'شما مدل دیابت را انتخاب کردید. لطفاً یکی از گزینه‌های زیر را انتخاب کنید:')
            append_message(chat_history, 'bot', '1. آپلود تصویر آزمایش')
            append_message(chat_history, 'bot', '2. پر کردن اطلاعات به صورت دستی')
            diabetes_state['current_step'] = 'awaiting_choice'
        else:
            append_message(chat_history, 'bot', 'شما مدل فیلم را انتخاب کردید. لطفا نام فیلم یا ژانر را وارد کنید (فارسی یا انگلیسی).')

        context_updates['selected_model'] = selected_model
        return context_updates

    if selected_model == 'diabetes':
        user_input = to_english_digits(request.POST.get('user_input', '').strip())

        if diabetes_state.get('current_step') == 'awaiting_choice':
            if user_input == '1':
                append_message(chat_history, 'user', 'آپلود تصویر آزمایش')
                append_message(chat_history, 'bot', 'لطفاً تصویر آزمایش خود را آپلود کنید.')
                diabetes_state['current_step'] = 'awaiting_image'
            elif user_input == '2':
                append_message(chat_history, 'user', 'پر کردن اطلاعات دستی')
                append_message(chat_history, 'bot', 'خب، اطلاعات را به صورت قدم به قدم وارد می‌کنیم.\n تعداد دفعات بارداری را وارد کنید. اگر مرد هستید یا تجربه بارداری ندارید، 0 وارد کنید:')
                diabetes_state['current_step'] = 'collecting_data'
                diabetes_state['collected_data'] = {}
                diabetes_state['remaining_fields'] = DiabetesModel.REQUIRED_FIELDS.copy()
                diabetes_state['current_field'] = diabetes_state['remaining_fields'].pop(0)
            else:
                append_message(chat_history, 'bot', 'لطفاً عدد 1 یا 2 را وارد کنید.')

        elif diabetes_state.get('current_step') == 'awaiting_image':
            if 'test_image' in request.FILES:
                upload_form = DiabetesUploadForm(request.POST, request.FILES)
                if upload_form.is_valid():
                    image = upload_form.cleaned_data['test_image']
                    prediction = handler.predict('diabetes', {'image': image})
                    append_message(chat_history, 'user', 'عکس آزمایش ارسال شد')
                    if prediction.get('status') == 'success':
                        append_message(chat_history, 'bot', f'{"متاسفانه باید بگم که شما دیابت دارید" if prediction.get("result") == 1 else "خوشبختانه شما دیابت ندارید"}')
                    elif prediction.get('status') == 'incomplete':
                        missing = prediction.get('missing_fields', [])
                        append_message(chat_history, 'bot', f'برخی فیلدها از تصویر استخراج نشدند: {", ".join(missing)}. لطفاً آنها را وارد کنید یا تصویر بهتری ارسال کنید.')
                    else:
                        append_message(chat_history, 'bot', prediction.get('message', 'خطایی رخ داد.'))
                    diabetes_state['current_step'] = None
                else:
                    append_message(chat_history, 'bot', 'فرم تصویر معتبر نیست. لطفاً دوباره تلاش کنید.')

        elif diabetes_state.get('current_step') == 'collecting_data':
            current_field = diabetes_state.get('current_field')
            if not current_field:
                append_message(chat_history, 'bot', 'خطا در وضعیت جمع‌آوری داده — لطفا دوباره شروع کنید.')
                diabetes_state['current_step'] = None
            else:
                raw = request.POST.get('user_input', '').strip()
                if raw:
                    append_message(chat_history, 'user', raw)
                try:
                    if current_field in ['Pregnancies', 'Glucose', 'BloodPressure', 'SkinThickness', 'Insulin', 'Age']:
                        val = int(to_english_digits(raw))
                    else:
                        val = float(to_english_digits(raw).replace(',', '.'))

                    diabetes_state['collected_data'][current_field] = val

                    if not diabetes_state.get('remaining_fields'):
                        prediction = handler.predict('diabetes', diabetes_state['collected_data'])
                        if prediction.get('status') == 'success':
                            append_message(chat_history, 'bot', f'{"متاسفانه باید بهتون بگم که شما دیابت دارید" if prediction.get("result") == 1 else "تبریک میگم شما دیابت ندارید"}')
                        else:
                            append_message(chat_history, 'bot', prediction.get('message', 'خطا در پیش‌بینی'))
                        diabetes_state['current_step'] = None
                    else:
                        next_field = diabetes_state['remaining_fields'].pop(0)
                        diabetes_state['current_field'] = next_field
                        field_messages = {
                            'Pregnancies': 'تعداد دفعات بارداری را وارد کنید. اگر مرد هستید یا تجربه بارداری ندارید، 0 وارد کنید.',
                            'Glucose': 'مقدار قند خون (mg/dL) را وارد کنید (قند خون طبیعی کمتر از 100 است).',
                            'BloodPressure': 'فشار خون (mm Hg) خود را بنویسید (معمولاً حدود 80 است).',
                            'SkinThickness': 'ضخامت چین پوستی (میلی‌متر) بدنتان را وارد کنید (معمولا ضخامت پوستی  2 میلی متر است).',
                            'Insulin': 'مقدار انسولین (mu U/ml) بدنتان را ارسال کنید (برای یک انسان عادی، حدود 80 است).',
                            'BMI': 'شاخص توده بدنی (BMI) را بنویسید (اگر نمی‌دانید: وزن (kg) ÷ (قد(m))²)',
                            'DiabetesPedigreeFunction': (
                                "شاخص سابقه خانوادگی دیابت:\n"
                                "- اگر هیچ‌کس در خانواده مبتلا نیست: 0.0\n"
                                "- اگر یکی‌دو نفر از اقوام نزدیک مبتلا هستند: حدود 0.5\n"
                                "- اگر بیش از دو نفر مبتلا هستند: حدود 1.0\n"
                                "- اگر بیشتر اعضای خانواده مبتلا هستند: نزدیک 2.0"
                            ),
                            'Age': 'چند سال عمر کیده اید؟'
                        }
                        append_message(chat_history, 'bot', field_messages.get(next_field, f'لطفاً مقدار {next_field} را وارد کنید:'))
                except ValueError:
                    append_message(chat_history, 'bot', 'لطفاً یک عدد معتبر وارد کنید.')

        context_updates['diabetes_state'] = diabetes_state
        return context_updates

    if selected_model == 'movie':
        raw_input = request.POST.get('user_input', '').strip()

        if 'movie_options' in request.session and raw_input:
            if request.session.get('selected_model') == 'movie':
                append_message(chat_history, 'user', raw_input)
                try:
                    choice_idx = int(to_english_digits(raw_input)) - 1
                    options = request.session.get('movie_options', [])
                    if 0 <= choice_idx < len(options):
                        selected_title = options[choice_idx]
                        del request.session['movie_options']
                        if 'original_query' in request.session:
                            del request.session['original_query']

                        result = handler.predict('movie', {'title': selected_title})
                        if result.get('status') == 'success':
                            append_message(chat_history, 'bot', 'فیلم‌های پیشنهادی:')
                            for i, title in enumerate(result.get('titles', [])):
                                poster = None
                                posters = result.get('posters') or []
                                try:
                                    poster = posters[i]
                                except Exception:
                                    poster = None
                                if poster:
                                    append_message(chat_history, 'bot', f"{i + 1}. {title} — {poster}")
                                else:
                                    append_message(chat_history, 'bot', f"{i + 1}. {title}")
                        elif result.get('status') == 'need_confirmation':
                            options2 = result.get('options', [])
                            request.session['movie_options'] = options2
                            append_message(chat_history, 'bot', result.get('message', 'کدام یک؟'))
                            for i, opt in enumerate(options2):
                                append_message(chat_history, 'bot', f"{i + 1}. {opt}")
                        else:
                            append_message(chat_history, 'bot', result.get('message', 'خطا در دریافت پیشنهادات'))
                    else:
                        append_message(chat_history, 'bot', 'عدد وارد شده خارج از بازه گزینه‌هاست. لطفاً یک عدد معتبر وارد کنید.')
                except ValueError:
                    result = handler.predict('movie', {'title': raw_input})
                    if result.get('status') == 'success':
                        append_message(chat_history, 'bot', 'فیلم‌های پیشنهادی:')
                        for i, title in enumerate(result.get('titles', [])):
                            poster = None
                            posters = result.get('posters') or []
                            try:
                                poster = posters[i]
                            except Exception:
                                poster = None
                            if poster:
                                append_message(chat_history, 'bot', f"{i + 1}. {title} — {poster}")
                            else:
                                append_message(chat_history, 'bot', f"{i + 1}. {title}")
                    elif result.get('status') == 'need_confirmation':
                        options2 = result.get('options', [])
                        request.session['movie_options'] = options2
                        append_message(chat_history, 'bot', result.get('message', 'کدام یک؟'))
                        for i, opt in enumerate(options2):
                            append_message(chat_history, 'bot', f"{i + 1}. {opt}")
                    else:
                        append_message(chat_history, 'bot', result.get('message', 'خطا در پردازش درخواست'))
            return context_updates

        if raw_input:
            append_message(chat_history, 'user', raw_input)
            result = handler.predict('movie', {'title': raw_input})

            if result.get('status') == 'need_confirmation':
                options = result.get('options', [])
                request.session['movie_options'] = options
                request.session['original_query'] = raw_input
                append_message(chat_history, 'bot', result.get('message', 'کدام یک؟'))
                for i, option in enumerate(options):
                    append_message(chat_history, 'bot', f"{i + 1}. {option}")
                append_message(chat_history, 'bot', 'لطفاً عدد مربوط به فیلم مورد نظر را وارد کنید.')
            elif result.get('status') == 'success':
                append_message(chat_history, 'bot', 'فیلم‌های پیشنهادی:')
                for i, title in enumerate(result.get('titles', [])):
                    poster = None
                    posters = result.get('posters') or []
                    try:
                        poster = posters[i]
                    except Exception:
                        poster = None
                    if poster:
                        append_message(chat_history, 'bot', f"{i + 1}. {title} — {poster}")
                    else:
                        append_message(chat_history, 'bot', f"{i + 1}. {title}")
            elif result.get('status') == 'error':
                append_message(chat_history, 'bot', result.get('message', 'خطایی رخ داده است.'))

        return context_updates

    return context_updates


@csrf_exempt
def chat_view(request):
    if 'chat_history' not in request.session:
        request.session['chat_history'] = []

    if 'diabetes_state' not in request.session:
        request.session['diabetes_state'] = {
            'current_step': None,
            'collected_data': {},
            'remaining_fields': []
        }

    chat_history = request.session['chat_history']
    diabetes_state = request.session['diabetes_state']

    model_form = ModelSelectForm(request.POST or None)
    selected_model = request.session.get('selected_model', None)

    if request.method == 'POST':
        updates = process_user_post(request, chat_history, diabetes_state, selected_model)
        request.session['chat_history'] = chat_history
        request.session['diabetes_state'] = diabetes_state
        request.session.modified = True

        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'chat_history': chat_history,
                'selected_model': request.session.get('selected_model', None)
            })

    context = {
        'chat_history': chat_history,
        'selected_model': request.session.get('selected_model', None),
    }

    return render(request, 'chat.html', context)


@csrf_exempt
def api_send_message(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        user_input = data.get('message', '').strip()
        selected_model = data.get('model', request.session.get('selected_model', ''))

        if selected_model == 'movie' and user_input:
            result = handler.predict('movie', {'title': user_input})
            return JsonResponse({'success': True, 'result': result})

        return JsonResponse({
            'success': True,
            'response': 'پیام دریافت شد. (از طریق صفحهٔ چت اصلی تعامل بهتر پشتیبانی می‌شود)'
        })

    return JsonResponse({'success': False, 'error': 'Method not allowed'}, status=405)

@csrf_exempt
def clear_chat_history(request):
    if request.method == 'POST':
        request.session.pop('chat_history', None)
        request.session.pop('diabetes_state', None)
        request.session.modified = True
        return JsonResponse({'success': True})
    return JsonResponse({'success': False, 'error': 'Method not allowed'}, status=405)