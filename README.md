# anitube-ua-lib

## Description
- Parser for data from the site anitube.in.ua (EN)
- Парсер даних з сайту anitube.in.ua (UA)

## Required Libraries
- beautifulsoup4
- requests-cache

## Examples
```python
from anitube import AniTube

api = AniTube()

for anime in api.get_animes(limit=5):
    print(anime.name)

# Мрійливий хлопець - реаліст
# Мій щасливий шлюб
# Блукач Кеншін: Романтичне сказання про мечника епохи Мейджі
# Повсякденне життя безсмертного короля (Сезон 2)
# Зом 100: Сотня справ, які треба зробити перш ніж стати зомбаком
```

```python
from anitube import AniTube

api = AniTube()

animes = api.search_anime(search="Демон", limit=5)
for anime in animes:
    print(anime.name)

# Демоничка з нашого району
# 3х3 Ока: Легенда про Божественного Демона
# Однокімнатка героя та лорд-демона 1 рівня
# Клинок, який знищує демонів: Арка селище ковалів (3 сезон)
# Полювання короля демонів на свою дружину
```
