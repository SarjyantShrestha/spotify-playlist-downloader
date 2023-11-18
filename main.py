import os
from pydub import AudioSegment
import requests
from bs4 import BeautifulSoup
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
from mutagen.flac import FLAC
from mutagen.mp3 import MP3
from mutagen.id3 import ID3, APIC
import client_info
from tqdm import tqdm
import warnings


def search_songs(artist_name, track_name):
    search_url = f"https://slavart.gamesdrive.net/api/search?q={artist_name} {track_name}"
    response = requests.get(search_url)
    json_data = response.json()
    tracks = json_data.get('tracks', {})
    items = tracks.get('items', [])
    if items:
        my_track = items[0]

    id = my_track.get('id')
    return (id, track_name, artist_name)


def download_song(id, track_name, artist_name):
    download_url = f"https://slavart-api.gamesdrive.net/api/download/track?id={id}"
    response = requests.get(download_url, stream=True)
    print(response.status_code)

    file_path = os.path.join(
        "downloads", f"{artist_name} - {track_name}.flac")

    total_size = int(response.headers['content-length'])
    chunk_size = 1024

    with open(file_path, 'wb') as f:
        for chunk in tqdm(iterable=response.iter_content(chunk_size=chunk_size), desc=f"{track_name}", total=total_size/chunk_size, unit='KB'):
            if chunk:
                f.write(chunk)

    return file_path


def convert_to_mp3(file_path):
    flac_audio = AudioSegment.from_file(file_path, "flac")
    mp3_output_path = os.path.splitext(file_path)[0] + ".mp3"
    flac_audio.export(mp3_output_path, format="mp3")
    return mp3_output_path


def remove_flac():
    dir_name = "./downloads"
    test = os.listdir(dir_name)

    for item in test:
        if item.endswith(".flac"):
            os.remove(os.path.join(dir_name, item))


def get_metadata(path_flac, path_mp3):
    file = FLAC(path_flac)
    art = file.pictures[0].data
    audio = MP3(path_mp3)
    audio.tags.add(
        APIC(
            encoding=3,  # 3 is for utf-8
            mime='image/png',  # image/jpeg or image/png
            type=3,  # 3 is for the cover image
            desc=u'Cover',
            data=art
        )
    )
    audio.save()


if __name__ == "__main__":
    warnings.filterwarnings('ignore')  # ignore tqdmWarning
    sp = spotipy.Spotify(auth_manager=SpotifyClientCredentials(
        client_id=client_info.SPOTIFY_CLIENT_ID, client_secret=client_info.SPOTIFY_CLIENT_SECRET))

    PLAYLIST_ID = input(
        'Enter your playlist link (it must be a public playlist): ')
    results = sp.playlist_tracks(playlist_id=PLAYLIST_ID)
    tracks = results['items']
    total_items = results['total']
    print(f"Total songs detected: {total_items}")
    os.makedirs("downloads", exist_ok=True)
    for track in tracks:
        track_name = track['track']['name']
        artist_name = track['track']['artists'][0]['name']
        song_id = search_songs(track_name=track_name, artist_name=artist_name)
        flac_path = download_song(
            id=song_id[0], track_name=song_id[1], artist_name=song_id[2])
        mp3_path = convert_to_mp3(file_path=flac_path)
        get_metadata(path_flac=flac_path, path_mp3=mp3_path)
        remove_flac()
