# anitube

Python library for working with [AniTube](https://anitube.in.ua/) - anime resource 

## Installing
```
pip install git+https://github.com/Lorg0n/anitube-ua-lib/
```

## Usage
```python
# Import the library:
from anitube import AniTube

# Initialize:
anitube = AniTube()
# Log in
anitube.login("test", "qwerty")
# Search for anime:
results = anitube.search_anime("naruto", limit=10)

# Get anime details:
anime = results[0]
print(anime.name)
print(anime.description) 
print(anime.rating)

# Get anime screenshots:
screens = anime.get_big_screens() 
# or
screens = anime.get_small_screens()

# Get anime playlist:
playlist = anime.get_playlist()
print(playlist.json)

# Get anime list by filters:
anime_list = anitube.get_anime(
    cat=[6, 22],
    year=[2010, 2020], 
    sort='rating'
)
```

## Description
anitube-ua-lib is a Python library for convenient work with AniTube anime resource.

It allows you to:
- Search anime
- Get anime details like description, rating, categories, etc
- Get anime screenshots
- Get anime playlist (video links)
- Get anime list by filters: category, release year, rating, etc