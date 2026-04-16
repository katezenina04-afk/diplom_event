import re
from collections import defaultdict

from django.utils import timezone
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from .models import Event, Registration, Like, Favorite


# Слова, которые не надо учитывать как ключевые
EXCLUDED_WORDS = {
    'это', 'для', 'на', 'в', 'с', 'по', 'к', 'у', 'и', 'а', 'но', 'или',
    'также', 'еще', 'ещё', 'который', 'которые', 'которое', 'очень',
    'после', 'через', 'этого', 'такой', 'будет', 'были', 'если', 'при',
    'над', 'под', 'без', 'между', 'около', 'вместе',

    # мусорные слова адресов
    'улица', 'ул', 'проспект', 'пр', 'дом', 'дома', 'корпус', 'корп',
    'строение', 'район', 'город', 'область', 'поселок', 'посёлок',
    'площадь', 'набережная', 'переулок', 'шоссе', 'бульвар', 'микрорайон',

    # слишком общие слова
    'мероприятие', 'мероприятия', 'событие', 'события', 'проект',
    'система', 'пользователь', 'организация', 'участник', 'участники'
}


def get_event_text(event):
    """
    Собирает текст мероприятия для анализа.
    Адрес не включаем, чтобы он не попадал в ключевые слова рекомендаций.
    """
    text_parts = []

    if event.title:
        text_parts.append(event.title)

    if event.description:
        text_parts.append(event.description)

    if event.category:
        text_parts.append(event.category.name)

    return " ".join(text_parts).strip()


def get_user_behavior_text(user):
    """
    Формирует профиль интересов пользователя на основе его поведения.

    Веса сигналов:
    - attended     -> 4
    - favorite     -> 3
    - registered   -> 2
    - liked        -> 2
    """
    text_parts = []

    favorite_events = Event.objects.filter(favorites__user=user).distinct()
    liked_events = Event.objects.filter(likes__user=user).distinct()
    registered_events = Event.objects.filter(registrations__user=user).distinct()
    attended_events = Event.objects.filter(
        registrations__user=user,
        registrations__status='attended'
    ).distinct()

    for event in attended_events:
        event_text = get_event_text(event)
        if event_text:
            text_parts.extend([event_text] * 4)

    for event in favorite_events:
        event_text = get_event_text(event)
        if event_text:
            text_parts.extend([event_text] * 3)

    for event in registered_events:
        event_text = get_event_text(event)
        if event_text:
            text_parts.extend([event_text] * 2)

    for event in liked_events:
        event_text = get_event_text(event)
        if event_text:
            text_parts.extend([event_text] * 2)

    return " ".join(text_parts).strip()


def get_preferred_categories(user):
    """
    Считает предпочтения пользователя по категориям на основе поведения.
    Чем выше число, тем сильнее интерес к категории.
    """
    category_weights = defaultdict(float)

    favorite_events = Event.objects.filter(
        favorites__user=user
    ).select_related('category').distinct()

    liked_events = Event.objects.filter(
        likes__user=user
    ).select_related('category').distinct()

    registered_events = Event.objects.filter(
        registrations__user=user
    ).select_related('category').distinct()

    attended_events = Event.objects.filter(
        registrations__user=user,
        registrations__status='attended'
    ).select_related('category').distinct()

    for event in attended_events:
        if event.category_id:
            category_weights[event.category_id] += 4.0

    for event in favorite_events:
        if event.category_id:
            category_weights[event.category_id] += 3.0

    for event in registered_events:
        if event.category_id:
            category_weights[event.category_id] += 2.0

    for event in liked_events:
        if event.category_id:
            category_weights[event.category_id] += 2.0

    return category_weights


def get_event_popularity_score(event):
    """
    Оценка популярности мероприятия.
    Небольшой бонус, чтобы популярные события поднимались выше.
    """
    likes_count = event.likes.count()
    favorites_count = event.favorites.count()
    registrations_count = event.registrations.filter(is_invited=False).count()

    popularity_score = (
        likes_count * 0.01 +
        favorites_count * 0.02 +
        registrations_count * 0.015
    )

    return popularity_score


def get_event_recency_score(event):
    """
    Бонус за близость по времени.
    Ближайшие мероприятия полезнее рекомендовать выше.
    """
    if not event.start_datetime:
        return 0.0

    today = timezone.now().date()
    event_date = event.start_datetime.date()
    days_until_event = (event_date - today).days

    if 0 <= days_until_event <= 7:
        return 0.05
    if 8 <= days_until_event <= 30:
        return 0.02
    if 31 <= days_until_event <= 60:
        return 0.01

    return 0.0


def get_fallback_recommendations(limit=10):
    """
    Рекомендации для нового пользователя:
    ближайшие и более популярные опубликованные мероприятия.
    """
    events = Event.objects.filter(
        status='published',
        start_datetime__gt=timezone.now()
    ).distinct()

    event_scores = []

    for event in events:
        score = get_event_popularity_score(event) + get_event_recency_score(event)
        event_scores.append((event, score))

    event_scores.sort(key=lambda x: x[1], reverse=True)

    recommendations = []
    for event, score in event_scores[:limit]:
        recommendations.append({
            'event': event,
            'score': score,
            'percent_score': int(min(score * 100, 100)),
            'reasons': ['рекомендация сформирована на основе популярных и ближайших мероприятий']
        })

    return recommendations


def generate_recommendations(user, limit=10):
    """
    Генерирует рекомендации на основе поведения пользователя.

    Алгоритм:
    1. Собираем историю взаимодействия пользователя.
    2. Строим текстовый профиль интересов.
    3. Сравниваем его с будущими мероприятиями через TF-IDF + cosine similarity.
    4. Добавляем бонусы:
       - за любимую категорию,
       - за популярность,
       - за близость даты.
    """
    user_text = get_user_behavior_text(user)

    if not user_text:
        return get_fallback_recommendations(limit=limit)

    registered_event_ids = Registration.objects.filter(
        user=user
    ).values_list('event_id', flat=True)

    available_events = Event.objects.filter(
        status='published',
        start_datetime__gt=timezone.now()
    ).exclude(
        id__in=registered_event_ids
    ).select_related('category', 'creator').distinct()

    if not available_events.exists():
        return []

    event_texts = []
    events_list = []

    for event in available_events:
        event_text = get_event_text(event)
        if event_text:
            event_texts.append(event_text)
            events_list.append(event)

    if not event_texts:
        return []

    vectorizer = TfidfVectorizer(
        stop_words=list(EXCLUDED_WORDS),
        min_df=1,
        max_df=0.9,
        lowercase=True,
        ngram_range=(1, 2)
    )

    event_vectors = vectorizer.fit_transform(event_texts)
    user_vector = vectorizer.transform([user_text])

    similarities = cosine_similarity(user_vector, event_vectors)[0]
    preferred_categories = get_preferred_categories(user)

    recommendations = []

    for i, event in enumerate(events_list):
        text_score = float(similarities[i])

        # Бонус за категорию
        category_bonus = 0.0
        if event.category_id in preferred_categories:
            category_bonus = preferred_categories[event.category_id] * 0.02

        # Бонус за популярность
        popularity_bonus = get_event_popularity_score(event)

        # Бонус за близость даты
        recency_bonus = get_event_recency_score(event)

        final_score = text_score + category_bonus + popularity_bonus + recency_bonus

        # Порог отсечения слабых рекомендаций
        if final_score > 0.08:
            recommendations.append({
                'event': event,
                'score': final_score,
                'percent_score': int(min(final_score * 100, 100)),
                'reasons': explain_match(
                    user=user,
                    event=event,
                    text_score=text_score,
                    category_bonus=category_bonus,
                    popularity_bonus=popularity_bonus,
                    recency_bonus=recency_bonus,
                )
            })

    recommendations.sort(key=lambda x: x['score'], reverse=True)

    # Чтобы не было слишком много мероприятий одной категории подряд
    balanced_recommendations = []
    category_counter = defaultdict(int)

    for item in recommendations:
        category_id = item['event'].category_id
        if category_id is None or category_counter[category_id] < 3:
            balanced_recommendations.append(item)
            if category_id:
                category_counter[category_id] += 1

        if len(balanced_recommendations) >= limit:
            break

    return balanced_recommendations


def explain_match(user, event, text_score, category_bonus, popularity_bonus, recency_bonus):
    """
    Объясняет, почему мероприятие попало в рекомендации.
    Пишем человеческими причинами, а не слишком технически.
    """
    reasons = []

    # 1. Причина по категории
    preferred_categories = get_preferred_categories(user)
    if event.category_id in preferred_categories and event.category:
        reasons.append(
            f"вы часто интересуетесь мероприятиями категории «{event.category.name}»"
        )

    # 2. Причина по совпадению ключевых слов
    user_text = get_user_behavior_text(user).lower()
    event_text = get_event_text(event).lower()

    user_words = {
        word for word in re.findall(r'\b[а-яёa-zA-Z]{4,}\b', user_text)
        if word not in EXCLUDED_WORDS
    }

    event_words = {
        word for word in re.findall(r'\b[а-яёa-zA-Z]{4,}\b', event_text)
        if word not in EXCLUDED_WORDS
    }

    common_words = list(user_words & event_words)
    if common_words:
        reasons.append(
            f"совпадают интересующие вас темы: {', '.join(common_words[:3])}"
        )

    # 3. Причина по популярности
    if popularity_bonus >= 0.05:
        reasons.append("мероприятие пользуется популярностью у пользователей")

    # 4. Причина по близкой дате
    if recency_bonus >= 0.02:
        reasons.append("мероприятие состоится в ближайшее время")

    # 5. Если ничего не нашлось — резервная причина
    if not reasons:
        percent = int(min(text_score * 100, 100))
        reasons.append(f"мероприятие имеет высокую общую релевантность: {percent}%")

    return reasons[:3]