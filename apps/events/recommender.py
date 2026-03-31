import re
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from django.db.models import Q
from .models import Event, Category
from accounts.models import User


def get_user_profile_text(user):
    """Собирает текст из профиля пользователя для ML-анализа"""
    text_parts = []
    
    # Навыки
    if user.skills:
        text_parts.append(user.skills)
    
    # Опыт
    if user.experience:
        text_parts.append(user.experience)
    
    # Специализация (категории)
    specializations = list(user.specialization.values_list('name', flat=True))
    text_parts.extend(specializations)
    
    return " ".join(text_parts)


def get_event_text(event):
    """Собирает текст мероприятия для ML-анализа"""
    text_parts = []
    
    # Название и описание
    text_parts.append(event.title)
    if event.description:
        text_parts.append(event.description)
    
    # Категории
    categories = list(event.categories.values_list('name', flat=True))
    text_parts.extend(categories)
    
    return " ".join(text_parts)


def generate_recommendations(user, limit=5):
    """
    Генерирует ML-рекомендации для специалиста
    Использует TF-IDF + косинусную близость
    """
    from django.utils import timezone
    from .models import Event, Registration, Response
    
    # Получаем текст профиля пользователя
    user_text = get_user_profile_text(user)
    
    # Если профиль пустой — нет рекомендаций
    if not user_text.strip():
        return []
    
    # Мероприятия, на которые пользователь уже записан или приглашён
    registered_events = Registration.objects.filter(
        user=user
    ).values_list('event_id', flat=True)
    
    # Мероприятия, на которые пользователь уже откликался (если есть)
    responded_events = []
    if hasattr(user, 'responses'):
        responded_events = user.responses.filter(
            status__in=['accepted', 'pending']
        ).values_list('vacancy__event_id', flat=True)
    
    # Доступные мероприятия (опубликованные и предстоящие)
    available_events = Event.objects.filter(
        status='published',
        start_datetime__gt=timezone.now()
    ).exclude(
        id__in=registered_events
    ).exclude(
        id__in=responded_events
    )
    
    if not available_events:
        return []
    
    # Создаём список текстов мероприятий
    event_texts = []
    events_list = []
    for event in available_events:
        event_texts.append(get_event_text(event))
        events_list.append(event)
    
    # TF-IDF векторизация
    vectorizer = TfidfVectorizer(
        stop_words=['это', 'для', 'на', 'в', 'с', 'по', 'к', 'у', 'и', 'а', 'но', 'или', 'также', 'еще', 'который', 'которое', 'которые'],
        min_df=1,
        max_df=0.9,
        lowercase=True,
        ngram_range=(1, 2)  # учитываем и биграммы
    )
    
    # Обучаем векторизатор на текстах мероприятий
    event_vectors = vectorizer.fit_transform(event_texts)
    
    # Векторизуем профиль пользователя
    user_vector = vectorizer.transform([user_text])
    
    # Вычисляем косинусную близость
    similarities = cosine_similarity(user_vector, event_vectors)[0]
    
    # Собираем результаты
    recommendations = []
    for i, event in enumerate(events_list):
        score = similarities[i]
        if score > 0.05:  # минимальный порог
            recommendations.append({
                'event': event,
                'score': score,
                'percent_score': int(score * 100),
                'reasons': explain_match(user_text, get_event_text(event), score)
            })
    
    # Сортируем по убыванию
    recommendations.sort(key=lambda x: x['score'], reverse=True)
    
    return recommendations[:limit]


def explain_match(user_text, event_text, score):
    """Объясняет, почему мероприятие подходит"""
    reasons = []
    user_lower = user_text.lower()
    event_lower = event_text.lower()
    
    # 1. Проверяем тематики (категории)
    from .models import Category
    for cat in Category.objects.all():
        cat_name = cat.name.lower()
        if cat_name in user_lower and cat_name in event_lower:
            reasons.append(f"тематика «{cat.name}» соответствует вашим интересам")
            break
    
    # 2. Ищем общие ключевые слова
    user_words = set(re.findall(r'\b[а-яё\w]{4,}\b', user_lower))
    event_words = set(re.findall(r'\b[а-яё\w]{4,}\b', event_lower))
    common = user_words & event_words
    if common:
        reasons.append(f"совпадают ключевые слова: {', '.join(list(common)[:3])}")
    
    # 3. Если нет конкретных совпадений, показываем процент
    if not reasons:
        reasons.append(f"общая релевантность: {int(score * 100)}%")
    
    return reasons[:3]  # максимум 3 причины