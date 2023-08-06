import anitube as at

api = at.AniTube()
animes = api.search_anime('Революціонерка Утена', limit=1)
for anime in animes:
    print(anime.name)
    print(anime.get_playlist().json)



