from flask import Flask, render_template, redirect, url_for, request
import urllib.request, urllib.parse, urllib.error
import twurl
import json
import ssl
import folium
import geopy

app = Flask(__name__)

TWITTER_URL = 'https://api.twitter.com/1.1/friends/list.json'

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE



def get_user_data(twitter_tag, number_of_locations):
    """ (str) -> (dict)

    Function returns python dict with user info based on @twitter_tag.
    """

    TWITTER_URL = 'https://api.twitter.com/1.1/friends/list.json'

    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE


    url = twurl.augment(TWITTER_URL,
                        {'screen_name': twitter_tag, 'count': number_of_locations})

    connection = urllib.request.urlopen(url, context=ctx)
    data = connection.read().decode()
    user_data_js = json.loads(data)

    return user_data_js

def location_to_coords(location):
    """ (str) -> (tuple)

    Function to get coordinates from a location recursively, in case
    GeoPy raises an error
    """
    geolocator = geopy.Nominatim(user_agent="myGeolocator", timeout=10)

    user_location_obj = geolocator.geocode(location)
    if user_location_obj is not None:
        return user_location_obj.latitude, user_location_obj.longitude


def get_user_location_set(user_data):
    """ (dict) -> (set)

    Function get location of each user and returns it as a set of tuples.
    """

    user_location_set = set()

    for user in user_data['users']:

        if len(user["location"]) > 1:
            user_location_set.add((user["screen_name"], location_to_coords(user["location"])))

    return user_location_set

def generate_map(user_coords):
    """ (set) -> {generate .html}

    Function generates .html folium map of user coordinates.
    Each location is marked with user name.
    """

    map = folium.Map(location=[49.842957, 24.031111], zoom_start=3)
    user_location_group = folium.map.FeatureGroup(name="Friends' locations")

    while user_coords:

        user = user_coords.pop()
        try:
            folium.Marker(
                location=[user[1][0], user[1][1]],
                popup=user[0],
                icon=folium.Icon(icon='cloud')
            ).add_to(user_location_group)
        except:
            continue

    user_location_group.add_to(map)
    map.add_child(folium.LayerControl())

    map.save('templates/map.html')

@app.route("/map")
def map():
    return render_template("map.html")

@app.route("/", methods=["POST", "GET"])
def get_data():
    if request.method == "POST":
        twitter_name = request.form["twitter_tag"]
        locations_num = request.form["locations_num"]
        user_data = get_user_data(twitter_name, locations_num)
        user_coords = get_user_location_set(user_data)

        generate_map(user_coords)

        return redirect(url_for("map"))
    else:
        return render_template("get_data.html")

if __name__ == "__main__":

    app.run(debug=True)
    app.config['TEMPLATES_AUTO_RELOAD'] = True
