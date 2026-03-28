# Как встроить AI-ассистента в ваше Django-приложение

## Важное уточнение

AI-ассистент нельзя «встроить» так, чтобы он сам без контроля менял ваш код и файлы на компьютере.

Но можно встроить в приложение чат-ассистента через OpenAI API:
- пользователь пишет вопрос в интерфейсе,
- сервер отправляет запрос в API,
- ответ показывается в приложении.

## Минимальный план интеграции

1. Получить API-ключ OpenAI.
2. Добавить ключ в переменные окружения (`OPENAI_API_KEY`).
3. Создать Django view для чата (POST endpoint).
4. Добавить страницу/виджет чата в шаблон.
5. Ограничить права и контекст (не отправлять приватные данные без необходимости).

## Пример server-side (упрощённо)

```python
# apps/assistant/views.py
import os
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from openai import OpenAI

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

@csrf_exempt
@require_POST
def chat(request):
    prompt = request.POST.get("message", "")
    if not prompt:
        return JsonResponse({"error": "message is required"}, status=400)

    response = client.responses.create(
        model="gpt-5.3-codex",
        input=prompt,
    )
    return JsonResponse({"answer": response.output_text})
```

## Что важно по безопасности

- Ограничить длину запросов и rate-limit.
- Логировать ошибки без хранения секретов.
- Фильтровать персональные данные перед отправкой в API.
- Для админских действий использовать подтверждение пользователя, а не автодействия.

## Как использовать ассистента эффективно

- Для генерации черновиков текстов/описаний.
- Для объяснений пользователям в интерфейсе.
- Для подсказок по мероприятиям и FAQ.
- Для рекомендаций (отдельный модуль аналитики/AI).

