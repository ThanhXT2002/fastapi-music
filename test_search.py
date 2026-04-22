import concurrent.futures
from ytmusicapi import YTMusic

yt = YTMusic()

def fallback_search(query):
    with concurrent.futures.ThreadPoolExecutor() as executor:
        f_songs = executor.submit(yt.search, query, filter="songs", limit=10)
        f_artists = executor.submit(yt.search, query, filter="artists", limit=5)
        f_albums = executor.submit(yt.search, query, filter="albums", limit=5)
        
        songs = f_songs.result()
        artists = f_artists.result()
        albums = f_albums.result()
        
        return songs + artists + albums

try:
    print("Searching parallel...")
    res = fallback_search("son tung mtp")
    print("Success! Got", len(res), "results")
    # Check what types are returned
    types = set([r.get('resultType') for r in res])
    print("Result types:", types)
except Exception as e:
    import traceback
    traceback.print_exc()
