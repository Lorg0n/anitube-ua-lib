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
from anitube import AniTube
import json

api = AniTube()

anime = api.search_anime("МОБІЛЬНА БРОНЯ ҐАНДАМ: ЗЕТА")[0]
playlist = anime.get_playlist()
print(json.dumps(playlist.json, indent=4, ensure_ascii=False))

# {
#     "ПЛЕЄР AS***": {
#         "01. Чорний Ґандам": "https://*.*/*/*",
#         "02. Відправлення": "https://*.*/*/*",
#         "03. У капсулі": "https://*.*/*/*",
#         "04. Рішення Емми": "https://*.*/*/*",
#         "05. Батько та син": "https://*.*/*/*",
#         "06. На Землю": "https://*.*/*/*",
#         "07. Утеча зі Сторони 1": "https://*.*/*/*",
#         ...
#     }
# }
```
