import json
import math
import re
from datetime import timedelta
from enum import Enum

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

    def __init__(self, genre):
        if isinstance(genre, int):
            if genre in self.__cat:
                self.cat = genre
                self.string = self.__cat[genre]
            else:
                raise TypeError("There is no such category")

        elif isinstance(genre, str):
            self.cat = self.__get_cat(genre)
            self.string = genre

    def __str__(self):
        return str(self.cat)

    def __get_cat(self, string):
        for i in self.__cat:
            if self.__cat[i] == string:
                return i
        raise TypeError("There is no such category")


class Playlist:
    def __init__(self, session, structure: json):
        self.__session = session
        self.json = structure

    def __str__(self):
        return f'<Playlist: {self.__hash__(), len(self.json)}>'


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

        if data['success']:
            soup = BeautifulSoup(data['response'], 'html.parser')
            arr = soup.find_all('li', {'data-id': True, 'data-file': True})
            result = {}
            for item in arr:
                keys = item['data-id'].split('_')
                first_key = f"{keys[0]}_{keys[1]}"
                m = [first_key] + [f"{first_key}_{key}" for key in keys[2:]]
                m = [soup.find('li', {'data-id': e}).text for e in m]
                m.append(item.text)
                _set_nested(result, m, item['data-file'])

            return Playlist(session=self.__session, structure=result)

        else:
            data = self.__session.get(self.url)
            soup = BeautifulSoup(data.content, 'html.parser')
            result = {}

            for script in soup.find_all('script'):
                js_code = script.text
                if "RalodePlayer.init" in js_code:
                    raw_args = "[" + re.search(r'RalodePlayer\.init\((.*?)\);', js_code).group(1) + "]"
                    args = json.loads(raw_args)
                    for p in range(len(args[1])):
                        for e in range(len(args[1][p])):
                            item = args[1][p][e]
                            _set_nested(result, [args[0][p], item['name']], BeautifulSoup(item['code'], 'html.parser').find('iframe')['src'])

            return Playlist(self.__session, result)


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
        if len(articles) > 0:
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


def _set_nested(d, keys, value):
    for key in keys[:-1]:
        d = d.setdefault(key, {})
    d[keys[-1]] = value


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
