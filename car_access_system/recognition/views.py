from django.shortcuts import render, redirect
from django.http import JsonResponse
from PIL import Image
import numpy as np
import easyocr
import base64
from io import BytesIO
import cv2
import re


def preprocess_image(image):
    # Преобразуем изображение в градации серого
    gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)

    # Увеличиваем контрастность
    enhanced = cv2.equalizeHist(gray)

    # Применяем бинаризацию
    _, binary = cv2.threshold(enhanced, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

    return binary


def recognize_number(image):
    reader = easyocr.Reader(['en'])  # Поддержка английского языка
    results = reader.readtext(image)

    if not results:  # Если результат пустой
        return []

    # Если результаты есть, продолжаем
    recognized_text = []
    for (bbox, text, prob) in results:
        recognized_text.append({'text': text, 'probability': prob})
    return recognized_text

import re

def preprocess_recognized_number(text):

    pattern = r'[^0-9A-Za-zА-Яа-яRU\s]'
    # Удаляем все символы, которые не соответствуют паттерну
    cleaned_text = re.sub(pattern, '', text)
    return cleaned_text

def upload_image(request):
    if request.method == 'POST' and request.FILES.get('image'):
        # Получение файла из формы
        image_file = request.FILES['image']
        img = Image.open(image_file)

        # Конвертация в numpy array для easyocr
        img_np = np.array(img)

        # Распознавание номера
        results = recognize_number(img_np)

        # Если распознавание не дало результатов, возвращаем ошибку
        if not results:
            return render(request, 'recognition/upload.html', {'error': 'Не удалось распознать номер.'})

        # Сохраняем все результаты (включая с низкой вероятностью)
        request.session['results'] = results

        # Фильтрация текста: исключаем элементы с вероятностью меньше 0.4
        filtered_results = []
        for item in results:
            if item['probability'] >= 0.2:
                # Очищаем текст от нежелательных символов
                cleaned_text = preprocess_recognized_number(item['text'])
                filtered_results.append({'text': cleaned_text, 'probability': item['probability']})

        # Объединение отфильтрованных текстов
        recognized_text = ' '.join([item['text'] for item in filtered_results])

        # Сохраняем отфильтрованный текст в сессию для отображения на странице результатов
        request.session['recognized_text'] = recognized_text
        request.session['filtered_results'] = filtered_results

        # Сохранение изображения в формате base64 для отображения
        buffered = BytesIO()
        img.save(buffered, format="JPEG")
        img_base64 = base64.b64encode(buffered.getvalue()).decode('utf-8')

        # Сохраняем изображение в сессию
        request.session['image'] = img_base64

        # Перенаправление на страницу с результатами
        return redirect('show_result')

    return render(request, 'recognition/upload.html')  # Отображение формы загрузки


def show_result(request):
    # Получение результатов из сессии
    results = request.session.get('results', [])
    img_base64 = request.session.get('image', '')
    recognized_text = request.session.get('recognized_text', '')

    return render(request, 'recognition/result.html', {'results': results, 'image': img_base64, 'recognized_text': recognized_text})
