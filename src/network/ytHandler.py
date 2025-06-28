import json
from time import sleep
from urllib.parse import parse_qs, urlparse
import yt_dlp as yt
from models.enums import SongStatus
# from storage import cacheHandler as cahe

options = {
    'max_downloads' : 1
}
_dl = yt.YoutubeDL(options)
downloads: dict[str, SongStatus] = {}


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

def get_cache(prompt, is_link=False) -> tuple[str, str]:
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
        return '', ''

    # profit
    title = speciman['title'].lower()
    title = title.encode().decode('unicode_escape').encode('latin1').decode('utf-8') # encoding fix
    return speciman['id'], speciman['title'],


def get_playlist_cache(link) -> tuple[str, str, list[str]]:
    """returns id, title, [song_ids]"""
    ydl_opts = {
        'extract_flat': True,
        'dump_single_json': True,
    }

    with yt.YoutubeDL(ydl_opts) as ydl:
        print("extracting info")
        info = ydl.extract_info(link, download=False)
        if info is None:
            return '', '', []
        while info.get('_type') == 'url':
            print(info)
            print("getting deeper")
            info = ydl.extract_info(info['url'], download=False)
            if info is None:
                return '', '', []
        print("getting entries")
        entries = info.get('entries', [])
        print("getting tite")
        title = info['title']

        print(f"{info['id']}, {info['title']}, {[e['id'] for e in entries]}")

        if entries:
            print("returning")
            return info['id'], title, [entry['id'] for entry in entries]
        else:
            return '', '', []


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


def download(link, filename) -> bool:
    # skip dupes
    dupe = False
    while link in downloads.keys() and downloads[link] == SongStatus.DOWNLOADING:
        dupe = True
        print(f"waiting for {link}")
        sleep(1)
    if dupe:
        return True if downloads[link] == SongStatus.READY else False

    # track downloads to avoid dupes
    downloads[link] = SongStatus.DOWNLOADING

    options = {
        'format': 'bestaudio/best',
        'keepvideo': False,
        'outtmpl': filename
    }
    
    try:
        with(yt.YoutubeDL(options)) as ydl:
            ydl.download([link])
    except:
        downloads[link] = SongStatus.FAILED
        return False

    downloads[link] = SongStatus.READY
    print(f"returning success {link}")
    return True


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
    if "&list=" in link:
        return link[:link.find('&list=')]
    else:
        return link
