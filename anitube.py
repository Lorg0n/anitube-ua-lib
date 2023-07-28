import json
import math
import re
from datetime import timedelta

import requests_cache
from bs4 import BeautifulSoup


class Category:
    __cat = {
        70: "Антиутопія",
        73: "Бойове мистецтво",
        52: "Бойовик",
        10: "Буденність",
        14: "Готика",
        19: "Детектив",
        16: "Драма",
        65: "Еротика",
        15: "Еччі",
        4: "Жахи",
        29: "Зомбі",
        81: "Ісекай",
        60: "Історія",
        62: "Казка",
        5: "Комедія",
        61: "Кіберпанк",
        58: "Комодо",
        57: "Махо-шьоджьо",
        9: "Меха",
        20: "Містика",
        56: "Музичний",
        68: "Надприродне",
        47: "Пародія",
        3: "Пригоди",
        69: "Психологія",
        45: "Постапокаліптика",
        11: "Романтика",
        12: "Спорт",
        55: "Шьоджьо-аї",
        59: "Шьонен-аї",
        21: "Триллер",
        41: "Фантастика",
        6: "Фентезі",
        22: "Школа",
        49: "Шьоджьо",
        7: "Шьонен"
    }

    def __init__(self, x):
        if isinstance(x, int):
            if x in self.__cat:
                self.cat = x
                self.string = self.__cat[x]
            else:
                raise TypeError("There is no such category")

        elif isinstance(x, str):
            self.cat = self.__get_cat(x)
            self.string = x

    def __str__(self):
        return str(self.cat)

    def __get_cat(self, string):
        for i in self.__cat:
            if self.__cat[i] == string:
                return i
        raise TypeError("There is no such category")


class Episode:
    def __init__(self, session, name, url, player, voice=""):
        self.__session = session
        self.name = name
        self.url = url
        self.player = player
        self.voice = voice

    def __str__(self):
        return f'<anitube.Episode: "{self.name}">'


class Playlist:
    def __init__(self, session, episodes):
        self.__session = session
        self._episodes = episodes
        self._available_voices = None
        self._available_players = None

    def get_available_players(self):
        if self._available_players is None:
            players = []
            for episode in self._episodes:
                if episode.player not in players:
                    players.append(episode.player)
            self._available_players = players
            return players

        return self._available_players

    def get_available_voices(self):
        if self._available_voices is None:
            voices = []
            for episode in self._episodes:
                if episode.voice not in voices:
                    voices.append(episode.voice)
            self._available_voices = voices
            return voices
        return self._available_voices

    def filter(self, voices=[], players=[]):
        def check_voice(episode):
            return episode.voice in voices or not voices

        def check_player(episode):
            return episode.player in players or not players

        filtered = filter(
            lambda e: check_voice(e) and check_player(e),
            self._episodes)
        return Playlist(self.__session, filtered)

    def sort(self, ascending=False, reverse=False):
        episodes = self._episodes

        def get_ascending(e):
            number = int(re.findall(r'\d+', e.name)[0])
            return number

        if ascending:
            episodes = sorted(episodes, key=get_ascending)

        if reverse:
            episodes = sorted(episodes, reverse=reverse)

        return Playlist(self.__session, episodes)

    def __str__(self):
        return f'Playlist: [{", ".join(str(e) for e in self._episodes)}]'

    def __iter__(self):
        return iter(self._episodes)


class Anime:
    def __init__(self, session, name, poster, url, description, rating):
        self.__session = session
        self.name = name
        self.url = url
        self.description = description
        self.rating = rating
        self.poster = poster

    def get_big_screens(self):
        data = self.__session.get(self.url)
        soup = BeautifulSoup(data.content, 'html.parser')
        screen_div = soup.find('div', {'class': 'story_screens'})
        a_tag = screen_div.find_all('a')
        return [img['href'] for img in a_tag]

    def get_small_screens(self):
        data = self.__session.get(self.url)
        soup = BeautifulSoup(data.content, 'html.parser')
        screen_div = soup.find('div', {'class': 'story_screens'})
        imgs_tag = screen_div.find_all('img')
        return [img['src'] for img in imgs_tag]

    def get_voices(self):
        news_id = self.url.split('/')[-1].split('-')[0]
        data = self.__session.get(
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
                    session=self.__session,
                    name=item.text,
                    url=item['data-file'],
                    player=player,
                    voice=voice
                ))
        else:
            data = self.__session.get(self.url)
            soup = BeautifulSoup(data.content, 'html.parser')

            for script in soup.find_all('script'):
                js_code = script.text
                if "RalodePlayer.init" in js_code:
                    raw_args = "[" + re.search(r'RalodePlayer\.init\((.*?)\);', js_code).group(1) + "]"
                    args = json.loads(raw_args)
                    for p in range(len(args[1])):
                        for e in range(len(args[1][p])):
                            item = args[1][p][e]
                            episodes.append(Episode(
                                session=self.__session,
                                name=item['name'],
                                url=BeautifulSoup(item['code'], 'html.parser').find('iframe')['src'],
                                player=args[0][p]
                            ))
        return Playlist(self.__session, episodes)


class AniTube:
    def __init__(self):
        self._url = 'https://anitube.in.ua'
        self.__session = requests_cache.CachedSession('cache', expire_after=timedelta(minutes=15))

    def search_anime(self, search, limit=5):
        anime_list = []
        data = self.__session.post(f'{self._url}/anime/', params={
            'do': 'search',
            'subaction': 'search',
            'story': search
        })
        articles = _get_articles(data)
        try:
            for page in range(1, math.ceil(limit / len(articles)) + 1):
                articles = _get_articles(
                    self.__session.post(f'{self._url}/anime/', {
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
                    poster = f"{self._url}{article.find('span', {'class': 'story_post'}).find('img')['src']}"
                    rating = [
                        float(x) for x in
                        re.findall(r'\d+\.?\d*', article.find('div', {'class': 'div1'}).text)
                    ]

                    anime = Anime(self.__session, name, poster, url, descr,
                                  {'score': rating[0], 'max': rating[1], 'votes': rating[2]})
                    anime_list.append(anime)

                    if len(anime_list) == limit:
                        raise BreakLoops

        except BreakLoops:
            pass

        return anime_list

    def get_anime(
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
            'type': _get_value(types, ','),
            'sort': sort,
            'order': order,
            'r.real_rating': _get_value(rating, ';'),
            'r.year': _get_value(year, ';'),
            'm.tags': tags,
            'cat': _get_value(cat, ','),
            'ne-chpati': _get_value(ne_chpati, ',')
        }

        anime_list = []
        articles = _get_articles(self.__session.get(_get_url(f'{self._url}/f/', params)))

        try:
            for page in range(1, math.ceil(limit / len(articles)) + 1):
                articles = _get_articles(
                    self.__session.get(_get_url(f'{self._url}/f/', params, page))
                )

                if not articles:
                    raise BreakLoops

                for article in articles:
                    name = article.find('h2', {'itemprop': 'name'}).a.text
                    url = article.find('h2', {'itemprop': 'name'}).a['href']
                    descr = article.find('div', {'class': 'story_c_text'}).text
                    poster = f"{self._url}{article.find('span', {'class': 'story_post'}).find('img')['src']}"
                    rating = [
                        float(x) for x in
                        re.findall(r'\d+\.?\d*', article.find('div', {'class': 'div1'}).text)
                    ]

                    anime = Anime(self.__session, name, poster, url, descr,
                                  {'score': rating[0], 'max': rating[1], 'votes': rating[2]})
                    anime_list.append(anime)

                    if len(anime_list) == limit:
                        raise BreakLoops

        except BreakLoops:
            pass

        return anime_list


def _get_articles(response):
    soup = BeautifulSoup(response.content, 'html.parser')
    articles = soup.find('div', {'id': 'dle-content'}).find_all('article', {'class': 'story'})
    return articles if articles else []


def _get_url(url, params=None, page=1):
    if params:
        query = '/'.join([f'{k}={v}' for k, v in params.items() if v])
        return f'{url}/{query}/page/{page}/'
    return url


def _get_value(value, separator):
    if value is None:
        return None
    return separator.join(str(x) for x in value)


class BreakLoops(Exception):
    pass
