# diplom_event

Django-проект для планирования и публикации мероприятий.

## Как работать с изменениями от AI-ассистента

Ассистент вносит изменения **в git-репозиторий в текущей ветке**.
Если вы не видите изменения в VS Code, почти всегда причина в том, что:
1. открыт другой проект/папка,
2. выбрана другая ветка,
3. локальные коммиты не подтянуты.

### 1) Проверьте, что открыта правильная папка
Корень проекта должен содержать `manage.py`, папки `apps/`, `event_planner/`, `templates/`.

### 2) Проверьте ветку и последние коммиты
```bash
git branch --show-current
git log --oneline -n 10
```

### 3) Подтяните изменения
```bash
git pull
```

### 4) Убедитесь, что файлы обновились
```bash
git status
```


## Почему у вас виден только `Initial commit`

Если команда `git log --oneline -n 10` показывает только:
`2adedda Initial commit: Афиша мероприятий`,
значит ваш локальный репозиторий пока не содержит коммиты,
сделанные ассистентом в изолированной среде.

Это нормально: изменения не «телепортируются» автоматически в ваш компьютер.
Нужен перенос изменений одним из способов:
1. через pull request в ваш удалённый репозиторий,
2. через patch-файл (`git apply`),
3. через ручное копирование изменений по списку файлов.

## Быстрый запуск проекта

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

Откройте: `http://127.0.0.1:8000/`

## Что проверить после запуска

- Каталог специалистов: `/accounts/specialists/`
- Профиль пользователя: `/accounts/profile/`
- Редактирование профиля специалиста: `/accounts/specialist/edit/`

## Полезные команды проверки

```bash
python manage.py check
python manage.py test
```


## Как применять patch на Windows (CMD/PowerShell)

Команда `git apply <patch-file>` — это шаблон, а не буквальный текст.
Нужно подставить имя файла патча, например `changes.patch`.

### CMD
```cmd
git apply changes.patch
```

### PowerShell
```powershell
git apply .\changes.patch
```

### Если patch лежит в другой папке
```cmd
git apply C:\Users\You\Downloads\changes.patch
```

После применения:
```cmd
git status
python manage.py migrate
python manage.py runserver
```


### Ошибка `can't open patch` на Windows

Если видите:
`error: can't open patch 'changes.patch': No such file or directory`
значит Git не нашёл файл с таким именем.

Проверьте:
1. Вы находитесь в нужной папке: `cd C:\Диплом`
2. Файл действительно называется `changes.patch`, а не `changes.patch.txt`
3. Показать файлы в папке:
```cmd
dir
```
4. Если файл `changes.patch.txt`, переименуйте:
```cmd
ren changes.patch.txt changes.patch
```
5. После этого снова:
```cmd
git apply --check changes.patch
git apply changes.patch
```


### Ошибка `corrupt patch at line N`

Эта ошибка означает, что содержимое patch-файла повреждено (обычно при копировании из чата):
- попали лишние строки (например, ```patch / ```),
- потеряны строки в середине,
- сломались переносы строк.

Что сделать:
1. Удалить текущий `changes.patch`.
2. Создать patch заново в текстовом редакторе как **UTF-8**.
3. Убедиться, что в файле нет строк с тройными кавычками ```.
4. Проверить первые строки файла (должны начинаться с `diff --git ...`).
5. Проверка перед применением:
```cmd
git apply --check changes.patch
```

Если снова `corrupt patch`, применяйте изменения по частям (несколько небольших patch-файлов).
