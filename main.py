import anitube as at

api = at.AniTube()
anime = api.search_anime('БРЕХУН БРЕХУН')[0]

voices = anime.get_voices()
for i in voices:
    print(i.name, i.voice, i.player, i.types)


