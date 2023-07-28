# anitube-ua-lib

## Description
- Parser for data from the site anitube.in.ua (EN)
- Парсер даних з сайту anitube.in.ua (UA)

## Required Libraries
- beautifulsoup4
- requests-cache

## Examples
```python
import anitube as at

api = at.AniTube()
category_a = at.Category('Антиутопія')
category_b = 16  # Драма
anime_list = api.get_anime(cat=[category_a, category_b])

for anime in anime_list:
    print(anime.name)

# Богиня з косичками
# Подорож Кіно. Чарівний світ (2 сезон)
```

```python
import anitube as at

api = at.AniTube()
anime_list = api.search_anime("Я ПЕРЕРОДИВСЯ В ТОРГОВИЙ АВТОМАТ І ТЕПЕР БЛУКАЮ ПІДЗЕМЕЛЛЯМ")

for anime in anime_list:
    print(anime.name)
    playlist = anime.get_voices()
    for ep in playlist:
        print(f'- {ep.name}')

# Я переродився в торговий автомат і тепер блукаю підземеллям
# - 1 серія 
# ...
# - 4 серія
# Коли я переродився слизом (ОВА)
# - Епізод 1 - Гей! Дупці!
# ...
# - Епізод 5 - Солодке життя вчителя Рімуру (частина 3)
# Коли я переродився слизом / Про моє переродження в слиз
# - Серія 1: Штормовий Дракон Вельдора
# ...
# - Серія 24: Куро та Маска
# - Серія 24.5: Оповіді: Щоденник Вельдори
```
