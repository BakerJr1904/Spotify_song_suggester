import pandas as pd
import spotipy
from flask import Flask, render_template, request
from .Spotify import get_suggestions
from os import getenv


# Create a 'factory' for serving up the app when is launched
def create_app():
    # initializes our app
    app = Flask(__name__)

    # Database configurations
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False # Turn off verification when we request changes to db
    app.config["SQLALCHEMY_DATABASE_URI"] = getenv('DATABASE_URI')

    # Listen to a "route"
    # Make our "Home" "root" route. '/' is the home page route
    @app.route('/')
    def root():
        
        return render_template('index.html', title = 'Home')

    # @app.route('/search', methods=['POST'])
    # @app.route('/search/<user_input>', methods=['GET'])
    # def search(user_input=None):
    #     '''Resets DB, Search user-song, gather 30 related tracks and
    #     pull all the information we need for the model'''
    #     # remove everything from database
    #     DB.drop_all()

    #     # Create the database file initially
    #     DB.create_all()

    #     # Insert gatheres data into DB.
    #     songs_data = get_all_data(user_input)
    #     DB.session.add(songs_data)
    #     DB.session.commit()
    #     return render_template('index.html',title="Related songs search is complete")

    
    @app.route('/suggestions', methods=['POST'])
    def suggestions():
        user_input = request.values['user_input_song']
        suggestions = get_suggestions(user_input)
        suggestions = suggestions.reset_index(drop=True)

        dicts_list = []
        for i in range(len(suggestions)):
            dicts_list.append(dict(suggestions.iloc[i]))

        return render_template('suggestions.html',title='Results', suggestions=dicts_list)




    return app