import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import re
import json
import os

class Spotify:
    def __init__(self, playlist_url):
        self.load_config()
        self.spotify = self._initialize_spotify_client()
        self.playlist_id = self.extract_playlist_id(playlist_url)

    def _initialize_spotify_client(self):
        client_credentials_manager = SpotifyClientCredentials(client_id=self.client_id, client_secret=self.client_secret)
        return spotipy.Spotify(client_credentials_manager=client_credentials_manager)

    def extract_playlist_id(self, playlist_url):
        # Regular expression to extract the playlist ID from the URL
        pattern = r"(?:spotify:|https://[a-z]+\.spotify\.com/playlist/)([a-zA-Z0-9]+)(?:\?.*)?"
        match = re.match(pattern, playlist_url)
        if match:
            return match.group(1)
        else:
            return None

    def get_playlist_tracks(self, playlist_id):
        try:
            results = self.spotify.playlist_tracks(playlist_id)
            tracks = results['items']
            while results['next']:
                results = self.spotify.next(results)
                tracks.extend(results['items'])
            track_dict = {item['track']['name']: item['track']['artists'][0]['name'] for item in tracks}
            return track_dict
        except spotipy.exceptions.SpotifyException as e:
            print(f"An error occurred: {e}")
            return {}
        
    def get_song_length(self, track_name):
        track = self.spotify.search(q=f"track:{track_name}", type="track", limit=1)
        if track['tracks']['items']:
            return track['tracks']['items'][0]['duration_ms']
        else:
            return None
        
    def print_songs(self):
        track_dict = self.get_playlist_tracks(self.playlist_id)
        for i, track in enumerate(track_dict.keys(), 1):
            print(f"{i}. {track}")

    def get_track_preview_url(self, track_id):
        if track_id:
            track = self.spotify.track(track_id)
            return track['preview_url']
        else:
            return None
        
    def load_config(self):
        config_path = os.path.join(os.path.dirname(__file__), 'config.json')
        with open(config_path) as f:
            config = json.load(f)
        self.client_id = config['client_id']
        self.client_secret = config['client_secret']

def main():
    # Input: Spotify playlist URL
    playlist_url = input("Enter the Spotify playlist URL: ")

    # Initialize SpotifyPlaylist class
    spotify_playlist = Spotify(playlist_url)

    # Print track details
    spotify_playlist.print_songs()

if __name__ == "__main__":
    main()