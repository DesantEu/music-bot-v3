import json
from urllib.parse import parse_qs, urlparse
import yt_dlp as yt
from storage import cacheHandler as cahe

options = {
    'max_downloads' : 1
}
_dl = yt.YoutubeDL(options)


async def get_title(link:str):
    try:
        res = _dl.extract_info(link, download=False)
        with open("test.txt", "w+") as file:
            file.write(json.dumps(res))
    except:
        return -1

    if res:
        if 'ytsearch' in link:
            try:
                return res['entries'][0]['title']
            except:
                return -1
        try:
            return res['title']
        except:
            return -1
    else:
        return -1

def get_cache(prompt, is_link=False) -> cahe.CachedSong | None:
    speciman = {}

    # get video data
    if not is_link:
        res = _dl.extract_info(f"ytsearch1:{prompt}", download=False)
        if res:
            speciman = res["entries"][0]
    else:
        res = _dl.extract_info(prompt, download=False)
        if res:
            speciman = res

    # check that we have data
    if speciman == {}:
        return None

    # profit
    title = speciman['title'].lower()
    title = title.encode().decode('unicode_escape').encode('latin1').decode('utf-8') # encoding fix
    return cahe.CachedSong(speciman['id'],
                           speciman['title'],
                           [title] if is_link or prompt == title
                           else [prompt, title])

def get_playlist_cache(link) -> cahe.CachedSong | None:
    res = _dl.extract_info(link, download=False)

    if res:
        return cahe.CachedSong(res['id'],
                               res['title'],
                               [i['id'] for i in res['entries']],
                               is_playlist=True)

def get_mix_links(link, limit) -> list[str]:
    ydl_opts = {
    'extract_flat': True,
    'dump_single_json': True,
    'playlistend' : limit,
    # 'quiet': True,
    }

    with yt.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(link, download=False)
        entries = info.get('entries', [])
        video_urls = ['https://www.youtube.com/watch?v=' + entry['id'] for entry in entries]
        
        return video_urls


async def download(link, filename):
    #TODO: this is probably dumb

    options = {
        'format': 'bestaudio/best',
        'keepvideo': False,
        'outtmpl': filename
    }
    
    try:
        with(yt.YoutubeDL(options)) as ydl:
            ydl.download([link])
    except:
        return -1

    return 0


def get_id_from_link(link: str) -> str:
    parsed = urlparse(link)

    if parsed.hostname == 'youtu.be':
        return parsed.path[1:]
    if parsed.hostname in ('www.youtube.com', 'youtube.com'):
        if parsed.path == '/watch':
            p = parse_qs(parsed.query)
            return p['v'][0]
        if parsed.path[:7] == '/embed/':
            return parsed.path.split('/')[2]
        if parsed.path[:3] == '/v/':
            return parsed.path.split('/')[2]

    return ''


def get_id_from_playlist_link(link: str) -> str:
    begin = link[link.find('list=') + 5:]
    questions = begin.find('?')
    if questions > 0:
        begin = begin[:questions]

    ampersands = begin.find("&")
    if ampersands > 0:
        begin = begin[:ampersands]

    return begin


def remove_playlist_from_link(link: str) -> str:
    return link[:link.find('&list=')]
