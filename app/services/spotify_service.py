import os
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
from app.models import Contestant

class SpotifyService:
    def __init__(self):
        client_id = os.getenv("SPOTIFY_CLIENT_ID")
        client_secret = os.getenv("SPOTIFY_CLIENT_SECRET")
        
        if client_id and client_secret:
            self.sp = spotipy.Spotify(auth_manager=SpotifyClientCredentials(
                client_id=client_id,
                client_secret=client_secret
            ))
        else:
            self.sp = None

    def parse_url(self, url: str):
        if not self.sp:
            print("ERROR: Spotify credentials not found.")
            return []

        try:
            if "playlist" in url:
                return self._fetch_playlist(url)
            elif "album" in url:
                return self._fetch_album(url)
            elif "track" in url:
                return self._fetch_track(url)
            return []
        except Exception as e:
            print(f"Error parsing Spotify URL {url}: {e}")
            return []

    def _fetch_playlist(self, url):
        results = self.sp.playlist_items(url)
        contestants = []
        while results:
            for item in results['items']:
                track = item.get('track')
                if track and track.get('id'): 
                    contestants.append(self._format_track(track))
            if results['next']:
                results = self.sp.next(results)
            else:
                results = None
        return contestants

    def _fetch_album(self, url):
        album_info = self.sp.album(url)
        results = self.sp.album_tracks(url)
        contestants = []
        while results:
            for track in results['items']:
                track['album'] = {'images': album_info['images']} 
                contestants.append(self._format_track(track))
            if results['next']:
                results = self.sp.next(results)
            else:
                results = None
        return contestants

    def _fetch_track(self, url):
        track = self.sp.track(url)
        return [self._format_track(track)]

    def _format_track(self, track_obj):
        try:
            image_url = track_obj['album']['images'][0]['url']
        except (KeyError, IndexError, TypeError):
            image_url = "https://upload.wikimedia.org/wikipedia/commons/thumb/1/19/Spotify_logo_without_text.svg/2048px-Spotify_logo_without_text.svg.png"

        return Contestant(
            id=track_obj['external_urls']['spotify'],
            title=track_obj['name'],
            artist=track_obj['artists'][0]['name'],
            image_url=image_url,
            embed_html=None,  # DISABLED
            original_url=track_obj['external_urls']['spotify'],
            preview_url=track_obj.get('preview_url')
        )