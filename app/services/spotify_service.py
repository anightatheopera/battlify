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
        """
        Returns a list of Contestant objects.
        Can handle: Single Track, Album, or Playlist.
        """
        if not self.sp:
            print("ERROR: Spotify credentials not found.")
            return []

        try:
            # 1. Handle Playlists
            if "playlist" in url:
                return self._fetch_playlist(url)
            
            # 2. Handle Albums
            elif "album" in url:
                return self._fetch_album(url)
            
            # 3. Handle Single Track
            elif "track" in url:
                return self._fetch_track(url)
            
            return []

        except Exception as e:
            print(f"Error parsing Spotify URL {url}: {e}")
            return []

    def _fetch_playlist(self, url):
        # 1. Fetch first batch
        results = self.sp.playlist_items(url)
        contestants = []

        # 2. Loop through pagination
        while results:
            for item in results['items']:
                track = item.get('track')
                # Ensure valid track (sometimes local files return None)
                if track and track.get('id'): 
                    contestants.append(self._format_track(track))
            
            # 3. Check if there is a next page
            if results['next']:
                results = self.sp.next(results)
            else:
                results = None
                
        return contestants

    def _fetch_album(self, url):
        # Albums also have a limit (usually 50), so we paginate here too
        album_info = self.sp.album(url) # Get main album metadata first
        results = self.sp.album_tracks(url)
        contestants = []

        while results:
            for track in results['items']:
                # Inject the album image into the track object manually
                # (Album tracks endpoint doesn't return images per track)
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
        track_id = track_obj['id']
        # Safe way to get image (some local files/podcasts might lack images)
        try:
            image_url = track_obj['album']['images'][0]['url']
        except (KeyError, IndexError, TypeError):
            image_url = "https://upload.wikimedia.org/wikipedia/commons/thumb/1/19/Spotify_logo_without_text.svg/2048px-Spotify_logo_without_text.svg.png"

        # Construct the official Spotify Embed Iframe
        embed_html = (
            f'<iframe style="border-radius:12px" '
            f'src="https://open.spotify.com/embed/track/{track_id}?utm_source=generator" '
            f'width="100%" height="152" frameBorder="0" allowfullscreen="" '
            f'allow="autoplay; clipboard-write; encrypted-media; fullscreen; picture-in-picture" '
            f'loading="lazy"></iframe>'
        )

        return Contestant(
            id=track_obj['external_urls']['spotify'],
            title=track_obj['name'],
            artist=track_obj['artists'][0]['name'],
            image_url=image_url,
            embed_html=embed_html,
            original_url=track_obj['external_urls']['spotify']
        )