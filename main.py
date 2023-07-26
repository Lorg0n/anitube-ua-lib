from anitube import AniTube

api = AniTube()

animes = api.search_anime(search="Демон", limit=5)
for anime in animes:
    print(anime.name)