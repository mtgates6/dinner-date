from flask import Flask, request, render_template, jsonify
from flask_sqlalchemy import SQLAlchemy
from geopy.distance import geodesic
import  requests

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///restaurants.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

class Restaurant(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)


def geocode_address(address):
    response = requests.get(f'https://maps.googleapis.com/maps/api/geocode/json?address={address}&key=AIzaSyBcfyjXSEzoVa-PGE4c1G8HaZ7Tp6jHPzc')
    data = response.json()
    if response.status_code != 200 or not data['results']:
        raise ValueError(f"Geocoding API Error: {data.get('status', 'Unkown Error')}")

    location = data['results'][0]['geometry']['location']
    return (location['lat'], location['lng'])



def is_within_radius(lat1, lon1, lat2, lon2, radius_km):
    return geodesic((lat1,lon1),(lat2,lon2)) <= radius_km


@app.route('/')
def index():
    return render_template('index.html')

@app.route('/search' , methods=['POST'])
def search_restaurants():
    address1 = request.form.get('address1')
    address2 = request.form.get('address2')
    keyword = request.form.get('keyword')
    type = request.form.get('type')
    distance = int(request.form.get('distance'))
    #change to user variable input for distance
    radius_km = distance * 2

    try:
        lat1,lon1 = geocode_address(address1)
        lat2,lon2 = geocode_address(address2)
        app.logger.info(f"Address1: {address1}, Latitude: {lat1}, Longitude: {lon1}")
        app.logger.info(f"Address 2: {address2}, Latitude: {lat2}, Longitude: {lon2}")
        
    except ValueError as e:
        return jsonify({'error': str(e)}), 400


    places_api_url1 = f'https://maps.googleapis.com/maps/api/place/nearbysearch/json?location={lat1},{lon1}&radius={radius_km * 1000}&type={type}&keyword={keyword}&key=AIzaSyBcfyjXSEzoVa-PGE4c1G8HaZ7Tp6jHPzc'
    places_api_url2 = f'https://maps.googleapis.com/maps/api/place/nearbysearch/json?location={lat2},{lon2}&radius={radius_km * 1000}&type={type}&keyword={keyword}&key=AIzaSyBcfyjXSEzoVa-PGE4c1G8HaZ7Tp6jHPzc'
    
    response1 = requests.get(places_api_url1)
    response2 = requests.get(places_api_url2)

    data1 = response1.json()
    data2 = response2.json()
    app.logger.info(f"Type: {type} Keyword: {keyword} Radius: {radius_km}")
    if 'results' in data1:
        places1 = set(place['name'] for place in data1['results'])
        print(places1)
    if 'results' in data2:
        places2 = set(place['name'] for place in data2['results'])
        print(places2)

    intersection = places1 & places2
    
    clear_database()

    for name in intersection:
        restaurant = Restaurant(name=name)
        db.session.add(restaurant)

    db.session.commit()
    return render_template('results.html', results=list(intersection))

def clear_database():
    # Function to clear all data from the Restaurant table
    db.session.query(Restaurant).delete()
    db.session.commit()

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)