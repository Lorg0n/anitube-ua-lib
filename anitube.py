import json
import math
import re
from datetime import timedelta

import requests_cache
from bs4 import BeautifulSoup


class Category:
    __cat = {
        "70": "антиутопія",
        "73": "бойове мистецтво",
        "52": "бойовик",
        "10": "буденність",
        "14": "готика",
        "19": "детектив",
        "16": "драма",
        "65": "еротика",
        "15": "еччі",
        "4": "жахи",
        "29": "зомбі",
        "81": "ісекай",
        "60": "історія",
        "62": "казка",
        "5": "комедія",
        "61": "кіберпанк",
        "58": "комодо",
        "57": "махо-шьоджьо",
        "9": "меха",
        "20": "містика",
        "56": "музичний",
        "68": "надприродне",
        "47": "пародія",
        "3": "пригоди",
        "69": "психологія",
        "45": "постапокаліптика",
        "11": "романтика",
        "12": "спорт",
        "55": "шьоджьо-аї",
        "59": "шьонен-аї",
        "21": "триллер",
        "41": "фантастика",
        "6": "фентезі",
        "22": "школа",
        "49": "шьоджьо",
        "7": "шьонен"
    }

    def __init__(self, genre):
        if isinstance(genre, int):
            if genre in self.__cat:
                self.cat = genre.lower()
                self.string = self.__cat[genre]
            else:
                raise TypeError("There is no such category")

        elif isinstance(genre, str):
            self.cat = self.__get_cat(genre.lower())
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
    def __init__(self, session, name, poster, url, description, rating, year, episodes, categories, translation,
                 voice_actors):
        self.__session = session
        self.name = name
        self.url = url
        self.description = description
        self.rating = rating
        self.poster = poster
        self.year = year
        self.episodes = episodes
        self.categories = categories
        self.translation = translation
        self.voice_actors = voice_actors

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

    def get_playlist(self):
        return _get_playlist(self.__session, self.url)


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

                    year = 2023
                    episodes = []
                    voice_actors = []
                    categories = []
                    translation = []

                    advanced = article.find('div', {'class': 'story_infa'})
                    args = str(advanced).split('<hr/>')
                    for item in args:
                        i = BeautifulSoup(item, 'html.parser')
                        dt = i.find('dt')
                        if dt is not None:
                            code = BeautifulSoup(str(i).replace(str(dt), ''), 'html.parser')
                            if dt.text == 'Рік випуску аніме:':
                                year = code.find('a').text
                            elif dt.text == 'Серій:':
                                episodes_raw = [int(n) for n in re.findall(r'\d+', code.text)]
                                if len(episodes_raw) >= 2:
                                    episodes = {'current': episodes_raw[0], 'max': episodes_raw[1]}
                                else:
                                    episodes = {'current': None, 'max': None}
                            elif dt.text == 'Ролі озвучували:':
                                voice_actors = [n.text for n in code.find_all('a')]
                            elif dt.text == 'Категорія:':
                                categories = code.text.strip().split(', ')
                            elif dt.text == 'Переклад:':
                                translation = code.text.strip().split(', ')

                    poster = f"{self._url}{article.find('span', {'class': 'story_post'}).find('img')['src']}"
                    rating = [
                        float(x) for x in
                        re.findall(r'\d+\.?\d*', article.find('div', {'class': 'div1'}).text)
                    ]

                    anime = Anime(session=self.__session, name=name, poster=poster, url=url, description=descr,
                                  rating = {'score': rating[0], 'max': rating[1], 'votes': rating[2]}, year=year,
                                  episodes=episodes, categories=categories, translation=translation,
                                  voice_actors=voice_actors)
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

                        year = 2023
                        episodes = []
                        voice_actors = []
                        categories = []
                        translation = []

                        advanced = article.find('div', {'class': 'story_infa'})
                        args = str(advanced).split('<hr/>')
                        for item in args:
                            i = BeautifulSoup(item, 'html.parser')
                            dt = i.find('dt')
                            if dt is not None:
                                code = BeautifulSoup(str(i).replace(str(dt), ''), 'html.parser')
                                if dt.text == 'Рік випуску аніме:':
                                    year = code.find('a').text
                                elif dt.text == 'Серій:':
                                    episodes_raw = [int(n) for n in re.findall(r'\d+', code.text)]
                                    if len(episodes_raw) >= 2:
                                        episodes = {'current': episodes_raw[0], 'max': episodes_raw[1]}
                                    else:
                                        episodes = {'current': None, 'max': None}
                                elif dt.text == 'Ролі озвучували:':
                                    voice_actors = [n.text for n in code.find_all('a')]
                                elif dt.text == 'Категорія:':
                                    categories = code.text.strip().split(', ')
                                elif dt.text == 'Переклад:':
                                    translation = code.text.strip().split(', ')

                        poster = f"{self._url}{article.find('span', {'class': 'story_post'}).find('img')['src']}"
                        rating = [
                            float(x) for x in
                            re.findall(r'\d+\.?\d*', article.find('div', {'class': 'div1'}).text)
                        ]

                        anime = Anime(session=self.__session, name=name, poster=poster, url=url, description=descr,
                                      rating={'score': rating[0], 'max': rating[1], 'votes': rating[2]}, year=year,
                                      episodes=episodes, categories=categories, translation=translation,
                                      voice_actors=voice_actors)
                        anime_list.append(anime)

                        if len(anime_list) == limit:
                            raise BreakLoops
            except BreakLoops:
                pass
        return anime_list


def _get_playlist(session, url):
    news_id = url.split('/')[-1].split('-')[0]
    data = session.get(
        f"https://anitube.in.ua/engine/ajax/playlists.php",
        params={'news_id': news_id, 'xfield': 'playlist'}
    ).json()

    if data['success']:
        result = {}
        soup = BeautifulSoup(data['response'], 'html.parser')
        arr = soup.find_all('li', {'data-id': True, 'data-file': True})
        for item in arr:
            parts = item['data-id'].split("_")
            r = []
            for i in range(2, len(parts) + 1):
                r.append("_".join(parts[:i]))
            m = [soup.find('li', {'data-id': e, 'data-file': False}).text for e in r]
            m.append(item.text)
            _set_nested(result, m, item['data-file'])

        return Playlist(session=session, structure=result)

    else:
        data = session.get(url)
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
                        _set_nested(result, [args[0][p], item['name']],
                                    BeautifulSoup(item['code'], 'html.parser').find('iframe')['src'])

        return Playlist(session, result)


def _set_nested(d, keys, value):
    for key in keys[:-1]:
        d = d.setdefault(key, {})
    d[keys[-1]] = value


def _get_articles(response):
    try:
        soup = BeautifulSoup(response.content, 'html.parser')
        articles = soup.find('div', {'id': 'dle-content'}).find_all('article', {'class': 'story'})
        return articles if articles else []
    except:
        raise TypeError('Error! Site cant be opened.')


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