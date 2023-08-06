import anitube as at

api = at.AniTube()
animes = api.get_anime(limit=25)
for anime in animes:
    print(anime.name)
    print(anime.get_playlist().json)



