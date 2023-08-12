from bs4 import BeautifulSoup
from uuid import uuid4
import cloudscraper
import json
import m3u8
import os


HTTPS = 'https://'
BASE_URL = 'crunchyroll.com/'
API = 'api.'
ALL_ANIME = '/videos/anime/alpha?group=all'
api_params = {
    'version': '1.0',
    # ^ pode ser qualquer valor, wtf crunchyroll
    'access_token': 'LNDJgOit5yaRIWN',
    # ^ token de acesso a api pego do aplicativo da microsoft store
    'device_type': 'com.crunchyroll.windows.desktop',
    # ^ aplicativo da microsoft
    'device_id': str(uuid4())
    # ^ id do dispositivo, pode ser qualquer string mas pode ser encontrada em
    # https://www.crunchyroll.com/pt-br/acct/?action=devices
}
ANIME_INFO_STRING = "&locale=ptBR&fields=series.class,series.collection_count,series.description,series.landscape_image,series.media_count,series.media_type,series.name,series.portrait_image,series.publisher_name,series.rating,series.url,series.year&series_id="

scraper = cloudscraper.create_scraper(
    browser={
        'browser': 'firefox',
        'platform': 'windows',
        'mobile': False
    },
    # interpreter="js2py"
)


def get_anime_id(anime):
    '''
    raspa o link https://www.crunchyroll.com/pt-br/videos/anime/alpha?group=all para pegar o id e nome do anime
    '''
    html = scraper.get(HTTPS + BASE_URL + ALL_ANIME).text
    soup = BeautifulSoup(html, 'html.parser')
    tags = soup.find_all('a', class_="text-link ellipsis")
    for tag in tags:
        if anime == tag.get('title'):
            return tag.parent.get('group_id'), tag.get('title')

# anime_id, anime_title = get_anime_id("Magi")
# print(f'anime title: {anime_title}\nanime id: {anime_id}')


def start_session():
    '''
    pega o session_id gerado pela api necessário para usa-la, se logado com uma
    conta premium as arrays de stream dos episódios premium vem completas
    '''
    response = scraper.post(HTTPS + API + BASE_URL +
                            'start_session.0.json', params=api_params).text
    jsonObj = json.loads(response)
    return jsonObj['data']['session_id']


def get_anime_info(session_id, anime_id):
    '''
    pega informações como a url do anime na crunchyroll, numero de temporadas, distribuidora etc
    direto da api
    usage: anime_dict['key']
    '''
    response = scraper.get(HTTPS + API + BASE_URL +
                           'info.0.json?session_id=' + session_id + ANIME_INFO_STRING + anime_id).text
    jsonObj = json.loads(response)
    anime_dict = {
        'temporadas': jsonObj['data']['collection_count'],
        'sinopse': jsonObj['data']['description'],
        'episodios': jsonObj['data']['media_count'],
        'tipo': jsonObj['data']['media_type'],
        'nota': jsonObj['data']['rating'],
        'distribuidor': jsonObj['data']['publisher_name'],
        'url': jsonObj['data']['url'],
        'ano': jsonObj['data']['year'],
    }
    return anime_dict


def get_seasons(session_id, anime_id):
    '''
    lista as seasons do anime, coleta as collection ids e mais algumas coisas da api
    usage: seasons[index]['key']
    '''
    response = scraper.get(HTTPS + API + BASE_URL + "list_collections.0.json?session_id=" +
                           session_id + "&locale=ptBR&series_id=" + anime_id).text
    jsonObj = json.loads(response)
    seasons = {}
    for index in range(len(jsonObj['data'])):
        seasons[index] = jsonObj['data'][index]
    return seasons


def get_episodes_from_season(session_id, collection_id):
    '''
    pega os episódios de cada season do anime
    usage: episodes[index]['key']
    '''
    response = scraper.get(HTTPS + API + BASE_URL + "list_media.0.json?session_id=" +
                           session_id + "&locale=ptBR&collection_id=" + collection_id + "&limit=10000").text
    # entendi porra nenhuma desse parametro limite wtf
    jsonObj = json.loads(response)
    episodes = {}
    for index in range(len(jsonObj['data'])):
        episodes[index] = jsonObj['data'][index]
    return episodes


def get_streams(session_id, media_id):
    response = scraper.get(HTTPS + API + BASE_URL + "info.0.json?session_id=" + session_id +
                           "&locale=ptBR&fields=media.bif_url, media.premium_only, media.stream_data&media_id=" + media_id).text
    jsonObj = json.loads(response)
    bif_url = jsonObj['data']['bif_url']
    premium_only = jsonObj['data']['premium_only']
    m3u8Link = jsonObj['data']['stream_data']['streams'][0]['url']
    streams = {}
    playlists = m3u8.load(m3u8Link)
    for playlist in playlists.playlists:
        if playlist.uri.split("&")[-1] == "cdn=fy-prod":
            streams[playlist.stream_info.resolution[1]] = playlist.uri
        else:
            pass
    return streams, bif_url


def download_episode(streams, quality, bif_url, episodes, episode):
    # mp4 fica no indice 6 do array
    mp4 = streams[quality].split("/")[6].split("_")[1]
    tempBif = bif_url.split("bif", 2)
    tempBif[1] = mp4
    finalMp4 = ''.join(tempBif)
    finalMp4 = finalMp4.replace("https://", "https://fy.")
    with scraper.get(finalMp4, stream=True) as r:
        filename = os.getcwd() + "/" + \
            episodes[episode]['episode_number']+ " - " + episodes[episode]['name'] + ".mp4"
        with open(filename, 'wb') as f:
            for chunk in r.iter_content(chunk_size=5*1024):
                f.write(chunk)
    return filename


anime_id, anime_title = get_anime_id("Ranking of Kings")
session_id = start_session()
temporadas = get_seasons(session_id, anime_id)
episodios = get_episodes_from_season(
    session_id, temporadas[3]['collection_id'])
streams, bif_url = get_streams(session_id, episodios[0]['media_id'])
download_episode(streams, 240, bif_url, episodios, 0)


'''print(f
Titulo do anime: {anime_title})
print(f
Titulo da temporada: {temporadas[0]['name']}
)
for episodio in episodios:
    print(f
Episódio {episodios[episodio]['episode_number']} - {episodios[episodio]['name']}.)'''
