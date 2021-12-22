from sklearn.neighbors import NearestNeighbors
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
from os import getenv
import pandas as pd


# Connects to Spotify API
spotify = spotipy.Spotify(
    client_credentials_manager=SpotifyClientCredentials(
        getenv('CLIENT_ID'), 
        getenv('CLIENT_SECRET')
        )
    )

def input_track_uri(input_string):
    '''Takes a string performs a song search
    on Spotify API and returns the uri of that song'''
    song_uri = spotify.search(input_string, limit=1)['tracks']['items'][0]['uri']
    return song_uri

def get_30_tracks(input_track_uri):
    '''Pull the information of 30 songs from Spotify API
    # User-Imput-artist Top 10
    # 1 song from 10 related artists
    # 10 Spotify suggestions base on input song genre and artist '''

    # Get track info from API with uri                                                                           
    input_track_info = spotify.track(input_track_uri)

    # Get artist URI from track info
    artist_uri = input_track_info['artists'][0]['uri']

    # Get artist info from API with artist URI
    artist_info = spotify.artist(artist_uri)

    # Get artist genres list from artist info and taking one
    genre = artist_info.get('genres')[0]
    

    #   PULLING SONGS FROM API

    # Getting the User-Imput-artist Top 10 Tracks
    input_artist_top_10 = spotify.artist_top_tracks(artist_info.get('id'))['tracks']

    # Getting 1 song from 10 related artists
    related_artists = spotify.artist_related_artists(artist_info.get('id'))

    related_artists_ids = []
    for artist in related_artists['artists']:
        id = artist.get('id')
        related_artists_ids.append(id)

    related_artists_10 = []
    for id in related_artists_ids[:10]:
        track = spotify.artist_top_tracks(id)['tracks'][0]
        related_artists_10.append(track)

    # Selecting 10 from Spotify suggestions base on input song genre and artist
    suggested_list = spotify.recommendations([artist_uri], [genre])
    spotify_suggested_10 = suggested_list['tracks'][:10]

    # Joining the lists of 10 songs
    gathered_30 = [input_track_info] + related_artists_10 + spotify_suggested_10 + input_artist_top_10

    return gathered_30


def analize_tracks(gathered_tracks):
    '''Takes a list of tracks and all their general information
    and pull the audio feature analisis for each track from the Spotify API'''

    # Extracting and making a list with tracks IDs
    all_tracks_ids = []
    for track in gathered_tracks:
        all_tracks_ids.append(track['id'])

    # Pulling audio features analisis for each track
    gathered_30_analisis = spotify.audio_features(all_tracks_ids)
    
    return gathered_30_analisis

def get_suggestions(input_string):
    '''Takes an user input string search for a matching song
    in the Spotify API and return a dictionary with
    gathered information about 30 posible suggestions
    to play next base on that song's info'''

    # Search starting point
    input_song_uri = input_track_uri(input_string)

    # Gathered information from search
    gathered_30 = get_30_tracks(input_song_uri)
    gathered_30_analisis = analize_tracks(gathered_30)

    # Creating dfs (Preparing to Merge gathered information)
    general_data = pd.DataFrame(
        gathered_30,
        columns=['id','uri', 'external_urls', 'artists','album','name','popularity']
        )
    #droping user song from general_data df
    general_data = general_data[1:].reset_index(drop=True)

    features_data = pd.DataFrame(
        gathered_30_analisis,
        columns=['acousticness', 'danceability', 'energy',
       'instrumentalness', 'liveness', 'speechiness', 'valence']
                )
    
    # Praparing data to fit Model
    user_song = features_data[:1]
    
    gathered_songs = features_data[1:].reset_index(drop=True)

    # Instantiate NN Model
    neigh = NearestNeighbors(n_neighbors=2, radius=0.4)
    # Fit Nearest Neigbors Model
    nn = neigh.fit(gathered_songs)
    
    # Finding nearest neighbors to the user song
    distances, indexes = nn.kneighbors(X=user_song, n_neighbors=30, return_distance=True)
    # Preparing results to join general data
    results_df = pd.DataFrame({'model_distances':list(distances[0]), 'id':list(indexes[0])})

    # Joining Data
    gathered_results = gathered_songs.join(results_df).set_index('id', drop=True)
    # Reorder base on distances
    gathered_sorted = gathered_results.sort_values('model_distances')

    final_df = gathered_sorted.join(general_data)

    # CLEANING STRINGS FROM UNWANTED CHARACTERS

    #   Strip unwanted characters in name column strings
    # remove parenthesis and all inside them
    final_df['name'] = final_df['name'].str.replace(r" \(.*\)","")
    # splits strings using "-" and takes first half
    clean_names = []
    for name in final_df['name']:
        clean_name = name.split("-", 1)[0]
        clean_names.append(clean_name)

    final_df['name'] = clean_names

    #  REPLACING DICTIONARIES WITH NAMES

    # Artists column
    artists_names = []
    for i in range(30):
        artists_names.append(final_df['artists'][i][0]['name'])
    final_df['artists'] = artists_names

    # Album Column
    albums_names = []
    for i in range(30):
        albums_names.append(final_df['album'][i]['name'])
    final_df['album'] = albums_names

    # remove parenthesis and all inside them
    final_df['album'] = final_df['album'].str.replace(r" \(.*\)","")

    # Eliminating user song if is inside the results
    final_df = final_df[final_df['uri'] != input_song_uri]

    # Getting URLs
    final_df['external_urls'] = [url['spotify'] for url in final_df['external_urls']]

    return final_df[['name', 'artists', 'uri', 'external_urls']].head()



