import json
import math
import re
from datetime import timedelta

import requests_cache
from bs4 import BeautifulSoup

session = requests_cache.CachedSession('cache', expire_after=timedelta(minutes=15))


class Episode:
    def __init__(self, name, url, player, voice=""):
        self.name = name
        self.url = url
        self.player = player
        self.voice = voice

    def __str__(self):
        return f'<anitube.Episode: "{self.name}">'


class Playlist:
    def __init__(self, m):
        self.episodes = m

    def filter(self, voices=[], players=[]):
        def check_voice(episode):
            return episode.voice in voices or not voices

        def check_player(episode):
            return episode.player in players or not players

        filtered = filter(
            lambda e: check_voice(e) and check_player(e),
            self.episodes)
        return Playlist(filtered)

    def __str__(self):
        return f'Playlist: [{", ".join(str(e) for e in self.episodes)}]'

    def __iter__(self):
        return iter(self.episodes)


class Anime:
    def __init__(self, name, poster, url, description, rating):
        self.name = name
        self.url = url
        self.description = description
        self.rating = rating
        self.poster = poster

    def get_big_screens(self):
        data = session.get(self.url)
        soup = BeautifulSoup(data.content, 'html.parser')
        screen_div = soup.find('div', {'class': 'story_screens'})
        a_tag = screen_div.find_all('a')
        return [img['href'] for img in a_tag]

    def get_small_screens(self):
        data = session.get(self.url)
        soup = BeautifulSoup(data.content, 'html.parser')
        screen_div = soup.find('div', {'class': 'story_screens'})
        imgs_tag = screen_div.find_all('img')
        return [img['src'] for img in imgs_tag]

    def get_voices(self, ):
        news_id = self.url.split('/')[-1].split('-')[0]
        data = session.get(
            f"https://anitube.in.ua/engine/ajax/playlists.php",
            params={'news_id': news_id, 'xfield': 'playlist'}
        ).json()

        episodes = []
        if data['success']:
            soup = BeautifulSoup(data['response'], 'html.parser')

            for item in soup.find_all('li', {'data-id': True, 'data-file': True}):
                player = soup.find('li', {'data-id': item['data-id']}).text
                voice_id = item['data-id'].split('_')[:2]
                voice = soup.find('li', {'data-id': '_'.join(voice_id)}).text

                episodes.append(Episode(
                    name=item.text,
                    url=item['data-file'],
                    player=player,
                    voice=voice
                ))
        else:
            data = session.get(self.url)
            soup = BeautifulSoup(data.content, 'html.parser')

            for script in soup.find_all('script'):
                js_code = script.text
                if "RalodePlayer.init" in js_code:
                    raw_args = "[" + re.search(r'RalodePlayer\.init\((.*?)\);', js_code).group(1) + "]"
                    args = json.loads(raw_args)
                    for p in range(len(args[1])):
                        for e in range(len(args[1][p])):
                            item = args[1][p][e]
                            ep = Episode(name=item['name'],
                                         url=BeautifulSoup(item['code'], 'html.parser').find('iframe')['src'],
                                         player=args[0][p])
                            episodes.append(ep)
        return Playlist(episodes)


class AniTube:
    def __init__(self):
        self.url = 'https://anitube.in.ua'

    def search_anime(self, search, limit=5):
        anime_list = []
        data = session.post(f'{self.url}/anime/', params={
            'do': 'search',
            'subaction': 'search',
            'story': search
        })
        articles = get_articles(data)
        try:
            for page in range(1, math.ceil(limit / len(articles)) + 1):
                articles = get_articles(
                    session.post(f'{self.url}/anime/', {
                        'do': 'search',
                        'subaction': 'search',
                        'story': search,
                        'from_page': page,
                    })
                )

                if not articles:
                    raise BreakLoops

                for article in articles:
                    name = article.find('h2', {'itemprop': 'name'}).a.text
                    url = article.find('h2', {'itemprop': 'name'}).a['href']
                    descr = article.find('div', {'class': 'story_c_text'}).text
                    poster = f"{self.url}{article.find('span', {'class': 'story_post'}).find('img')['src']}"
                    rating = [
                        float(x) for x in
                        re.findall(r'\d+\.?\d*', article.find('div', {'class': 'div1'}).text)
                    ]

                    anime = Anime(name, poster, url, descr, {'score': rating[0], 'max': rating[1], 'votes': rating[2]})
                    anime_list.append(anime)

                    if len(anime_list) == limit:
                        raise BreakLoops

        except BreakLoops:
            pass

        return anime_list

    def get_animes(
            self,
            types=None,
            sort='date',
            order='desc',
            rating=None,
            year=None,
            tags=None,
            cat=None,
            ne_chpati=None,
            limit=11
    ):
        params = {
            'type': get_value(types, ','),
            'sort': sort,
            'order': order,
            'r.real_rating': get_value(rating, ';'),
            'r.year': get_value(year, ';'),
            'm.tags': tags,
            'cat': get_value(cat, ','),
            'ne-chpati': get_value(ne_chpati, ',')
        }

        anime_list = []
        articles = get_articles(session.get(get_url(f'{self.url}/f/', params)))

        try:
            for page in range(1, math.ceil(limit / len(articles)) + 1):
                articles = get_articles(
                    session.get(get_url(f'{self.url}/f/', params, page))
                )

                if not articles:
                    raise BreakLoops

                for article in articles:
                    name = article.find('h2', {'itemprop': 'name'}).a.text
                    url = article.find('h2', {'itemprop': 'name'}).a['href']
                    descr = article.find('div', {'class': 'story_c_text'}).text
                    poster = f"{self.url}{article.find('span', {'class': 'story_post'}).find('img')['src']}"
                    rating = [
                        float(x) for x in
                        re.findall(r'\d+\.?\d*', article.find('div', {'class': 'div1'}).text)
                    ]

                    anime = Anime(name, poster, url, descr, {'score': rating[0], 'max': rating[1], 'votes': rating[2]})
                    anime_list.append(anime)

                    if len(anime_list) == limit:
                        raise BreakLoops

        except BreakLoops:
            pass

        return anime_list


def get_articles(response):
    soup = BeautifulSoup(response.content, 'html.parser')
    articles = soup.find('div', {'id': 'dle-content'}).find_all('article', {'class': 'story'})

    return articles if articles else []


def get_url(url, params=None, page=1):
    if params:
        query = '/'.join([f'{k}={v}' for k, v in params.items() if v])
        return f'{url}/{query}/page/{page}/'

    return url


def get_value(value, separator):
    if value is None:
        return None

    return separator.join(str(x) for x in value)


class BreakLoops(Exception):
    pass
