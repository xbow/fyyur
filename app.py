#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

import sys
import json
import dateutil.parser
import babel
from flask import Flask, render_template, request, Response, flash, redirect, url_for
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from forms import *

#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')
db = SQLAlchemy(app)
migrate = Migrate(app, db)

#----------------------------------------------------------------------------#
# Models.
#----------------------------------------------------------------------------#

from models import *

#----------------------------------------------------------------------------#
# Filters.
#----------------------------------------------------------------------------#

def format_datetime(value, format='medium'):
  date = dateutil.parser.parse(value)
  if format == 'full':
      format="EEEE MMMM, d, y 'at' h:mma"
  elif format == 'medium':
      format="EE MM, dd, y h:mma"
  return babel.dates.format_datetime(date, format, locale='en')

app.jinja_env.filters['datetime'] = format_datetime

#----------------------------------------------------------------------------#
# Controllers.
#----------------------------------------------------------------------------#

@app.route('/')
def index():
  return render_template('pages/home.html')


#  Venues
#  ----------------------------------------------------------------

@app.route('/venues')
def venues():
  # sort venues by state, then city, so rows with identical city+state will be adjacent
  sorted_venues = Venue.query.order_by(Venue.state.asc()).order_by(Venue.city.asc()).all()

  data = []

  previous_city_state = {}

  for venue in sorted_venues:
    city_state = { 'city': venue.city, 'state': venue.state }

    # create a new section only if the city_state dict has changed
    if city_state != previous_city_state:
      data.append({
        'city': city_state['city'],
        'state': city_state['state'],
        'venues': []
      })
      previous_city_state = city_state

    # in any case, append a venue to the last section
    data[-1]['venues'].append({
      'id': venue.id,
      'name': venue.name,
      'num_upcoming_shows': Show.query.filter_by(venue_id=venue.id).filter(Show.start_time>datetime.now()).count()
    })      

  return render_template('pages/venues.html', areas=data)

@app.route('/venues/search', methods=['POST'])
def search_venues():

  term = request.form['search_term']
  results = Venue.query.filter(Venue.name.ilike(f'%{term}%')).all()
  
  data = []
  for venue in results:
    data.append({
      'id': venue.id,
      'name': venue.name,
      'num_upcoming_shows': Show.query.filter_by(venue_id=venue.id).filter(Show.start_time>datetime.now()).count()
    })
    
  response={
    'count': len(results),
    'data': data
  }

  return render_template('pages/search_venues.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):

  venue = Venue.query.get(venue_id)

  if not venue:
    return render_template('errors/404.html')

  past_shows_result = Show.query.filter_by(venue_id=venue.id).filter(Show.start_time<datetime.now()).all()
  upcoming_shows_result = Show.query.filter_by(venue_id=venue.id).filter(Show.start_time>datetime.now()).all()

  past_shows = []
  upcoming_shows = []

  for show in past_shows_result:
    past_shows.append({
      'artist_id': show.artist.id,
      'artist_name': show.artist.name,
      'artist_image_link': show.artist.image_link,
      'start_time': show.start_time.strftime('%m/%d/%Y, %H:%M:%S')
    })

  for show in upcoming_shows_result:
    upcoming_shows.append({
      'artist_id': show.artist.id,
      'artist_name': show.artist.name,
      'artist_image_link': show.artist.image_link,
      'start_time': show.start_time.strftime('%m/%d/%Y, %H:%M:%S')
  })

  data = {
    'id': venue.id,
    'name': venue.name,
    'genres': venue.genres,
    'city': venue.city,
    'state': venue.state,
    'address': venue.address,
    'phone': venue.phone,
    'website': venue.website,
    'facebook_link': venue.facebook_link,
    'seeking_talent': venue.seeking_talent,
    'seeking_description': venue.seeking_description,
    'image_link': venue.image_link,
    'past_shows': past_shows,
    'past_shows_count': len(past_shows),
    'upcoming_shows': upcoming_shows,
    'upcoming_shows_count': len(upcoming_shows),
  }

  return render_template('pages/show_venue.html', venue=data)

#  Create Venue
#  ----------------------------------------------------------------

@app.route('/venues/create', methods=['GET'])
def create_venue_form():
  form = VenueForm()
  return render_template('forms/new_venue.html', form=form)

@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
  # creating a new instance of Venue as outlined in the sqlalchemy docs:
  # https://docs.sqlalchemy.org/en/14/orm/tutorial.html#create-an-instance-of-the-mapped-class
  #
  # try / except block based on the todo_app excercise from the tutorial

  error = False
  try:
    venue = Venue(
      name = request.form['name'],
      city = request.form['city'],
      state = request.form['state'],
      address = request.form['address'],
      phone = request.form['phone'],
      image_link = request.form['image_link'],
      facebook_link = request.form['facebook_link'],
      genres = request.form.getlist('genres'),
      website = request.form['website_link'],
      seeking_talent = True if request.form.get('seeking_talent') else False,
      seeking_description = request.form['seeking_description']
    )
    db.session.add(venue)
    db.session.commit()  
  except:
    error = True
    db.session.rollback()
    print(sys.exc_info())
  finally:
    db.session.close()
  if error:
    flash('An error occurred. Venue ' + request.form['name'] + ' could not be listed.')
    return render_template('pages/home.html')
  else:
    flash('Venue ' + request.form['name'] + ' was successfully listed!')
    return render_template('pages/home.html')

@app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):

  venue = Venue.query.filter_by(id=venue_id)

  if venue.count() == 0:
    flash('No venue with id ' + venue_id + ' exists.')
    return render_template('errors/404.html')

  error = False
  try:
    venue.delete()
    db.session.commit()
  except:
    error = True
    db.session.rollback()
    print(sys.exc_info())
  finally:
    db.session.close()
  if error:
    flash('An error occurred. Venue ' + venue_id + ' could not be deleted.')
    return render_template('pages/venues.html')
  else: 
    # sadly, I could not find a way to get this url with the flash
    # message to load after pressing the button on the venues page,
    # but it works when sending a DELETE request in Postman.
    flash('Venue ' + venue_id + ' was successfully deleted!')
    return render_template('pages/venues.html')

#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():

  artists = Artist.query.all()

  data = []

  for artist in artists:
    data.append({
      'id': artist.id,
      'name': artist.name
    }) 

  return render_template('pages/artists.html', artists=data)

@app.route('/artists/search', methods=['POST'])
def search_artists():
  term = request.form['search_term']
  results = Artist.query.filter(Artist.name.ilike(f'%{term}%')).all()
  
  data = []
  for artist in results:
    data.append({
      'id': artist.id,
      'name': artist.name,
      'num_upcoming_shows': Show.query.filter_by(artist_id=artist.id).filter(Show.start_time>datetime.now()).count()
    })
    
  response={
    'count': len(results),
    'data': data
  }

  return render_template('pages/search_artists.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):

  artist = Artist.query.get(artist_id)

  if not artist:
    return render_template('errors/404.html')

  past_shows_result = Show.query.filter_by(artist_id=artist.id).filter(Show.start_time<datetime.now()).all()
  upcoming_shows_result = Show.query.filter_by(artist_id=artist.id).filter(Show.start_time>datetime.now()).all()

  past_shows = []
  upcoming_shows = []

  for show in past_shows_result:
    past_shows.append({
      'venue_id': show.venue.id,
      'venue_name': show.venue.name,
      'venue_image_link': show.venue.image_link,
      'start_time': show.start_time.strftime('%m/%d/%Y, %H:%M:%S')
    })

  for show in upcoming_shows_result:
    upcoming_shows.append({
      'venue_id': show.venue.id,
      'venue_name': show.venue.name,
      'venue_image_link': show.venue.image_link,
      'start_time': show.start_time.strftime('%m/%d/%Y, %H:%M:%S')
  })

  data = {
    'id': artist.id,
    'name': artist.name,
    'genres': artist.genres,
    'city': artist.city,
    'state': artist.state,
    'phone': artist.phone,
    'website': artist.website,
    'facebook_link': artist.facebook_link,
    'seeking_venue': artist.seeking_venue,
    'seeking_description': artist.seeking_description,
    'image_link': artist.image_link,
    'past_shows': past_shows,
    'past_shows_count': len(past_shows),
    'upcoming_shows': upcoming_shows,
    'upcoming_shows_count': len(upcoming_shows),
  }

  return render_template('pages/show_artist.html', artist=data)

#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
  form = ArtistForm()

  artist = Artist.query.get(artist_id)

  if not artist:
    return render_template('errors/404.html')

  data={
    'id': artist.id,
    'name': artist.name,
    'genres': artist.genres,
    'city': artist.city,
    'state': artist.state,
    'phone': artist.phone,
    'website': artist.website,
    'facebook_link': artist.facebook_link,
    'seeking_venue': artist.seeking_venue,
    'seeking_description': artist.seeking_description,
    'image_link': artist.image_link
  }  

  form.name.data = artist.name
  form.city.data = artist.city
  form.state.data = artist.state
  form.phone.data = artist.phone
  form.genres.data = artist.genres
  form.facebook_link.data = artist.facebook_link
  form.image_link.data = artist.image_link
  form.website_link.data = artist.website
  form.seeking_venue.data = artist.seeking_venue
  form.seeking_description.data = artist.seeking_description

  return render_template('forms/edit_artist.html', form=form, artist=data)

@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
  error = False
  artist = Artist.query.get(artist_id)

  try:
    artist.name = request.form['name']
    artist.city = request.form['city']
    artist.state = request.form['state']
    artist.phone = request.form['phone']
    artist.genres = request.form.getlist('genres')
    artist.facebook_link = request.form['facebook_link']
    artist.image_link = request.form['image_link']
    artist.website = request.form['website_link']
    artist.seeking_venue = True if 'seeking_venue' in request.form else False 
    artist.seeking_description = request.form['seeking_description']

    db.session.commit()
  except: 
    error = True
    db.session.rollback()
    print(sys.exc_info())
  finally:
    db.session.close()
  if error: 
    flash('An error occurred. Artist ' + request.form['name']+ ' could not be changed.')
  else: 
    flash('Artist ' + request.form['name'] + ' was successfully changed!')
    return redirect(url_for('show_artist', artist_id=artist_id))

@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
  form = VenueForm()

  venue = Venue.query.get(venue_id)

  if not venue:
    return render_template('errors/404.html')

  data={
    'id': venue.id,
    'name': venue.name,
    'genres': venue.genres,
    'city': venue.city,
    'state': venue.state,
    'address': venue.address,
    'phone': venue.phone,
    'website': venue.website,
    'facebook_link': venue.facebook_link,
    'seeking_talent': venue.seeking_talent,
    'seeking_description': venue.seeking_description,
    'image_link': venue.image_link
  }  

  form.name.data = venue.name
  form.city.data = venue.city
  form.state.data = venue.state
  form.phone.data = venue.phone
  form.genres.data = venue.genres
  form.address.data = venue.address
  form.facebook_link.data = venue.facebook_link
  form.image_link.data = venue.image_link
  form.website_link.data = venue.website
  form.seeking_talent.data = venue.seeking_talent
  form.seeking_description.data = venue.seeking_description

  return render_template('forms/edit_venue.html', form=form, venue=data)

@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
  error = False
  venue = Venue.query.get(venue_id)

  try:
    venue.name = request.form['name']
    venue.city = request.form['city']
    venue.state = request.form['state']
    venue.address = request.form['address']
    venue.phone = request.form['phone']
    venue.genres = request.form.getlist('genres')
    venue.facebook_link = request.form['facebook_link']
    venue.image_link = request.form['image_link']
    venue.website = request.form['website_link']
    venue.seeking_talent= True if 'seeking_talent' in request.form else False 
    venue.seeking_description = request.form['seeking_description']

    db.session.commit()
  except: 
    error = True
    db.session.rollback()
    print(sys.exc_info())
  finally:
    db.session.close()
  if error: 
    flash('An error occurred. Venue ' + request.form['name']+ ' could not be changed.')
  else: 
    flash('Venue ' + request.form['name'] + ' was successfully changed!')
    return redirect(url_for('show_venue', venue_id=venue_id))

#  Create Artist
#  ----------------------------------------------------------------

@app.route('/artists/create', methods=['GET'])
def create_artist_form():
  form = ArtistForm()
  return render_template('forms/new_artist.html', form=form)

@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
  # creating a new instance of Artist as outlined in the sqlalchemy docs:
  # https://docs.sqlalchemy.org/en/14/orm/tutorial.html#create-an-instance-of-the-mapped-class
  #
  # try / except block based on the todo_app excercise from the tutorial

  error = False
  try:
    artist = Artist(
      name = request.form['name'],
      city = request.form['city'],
      state = request.form['state'],
      phone = request.form['phone'],
      image_link = request.form['image_link'],
      facebook_link = request.form['facebook_link'],
      genres = request.form.getlist('genres'),
      website = request.form['website_link'],
      seeking_venue = True if request.form.get('seeking_venue') else False,
      seeking_description = request.form['seeking_description']
    )
    db.session.add(artist)
    db.session.commit()
  except:
    error = True
    db.session.rollback()
    print(sys.exc_info())
  finally:
    db.session.close()
  if error:
    flash('An error occurred. Artist ' + request.form['name'] + ' could not be listed.')
    return render_template('pages/home.html')
  else:
    flash('Artist ' + request.form['name'] + ' was successfully listed!')
    return render_template('pages/home.html')


#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():

  shows = Show.query.all()
  data = []

  for show in shows:
    data.append({
      'venue_id': show.venue.id,
      'venue_name': show.venue.name,
      'artist_id': show.artist.id,
      'artist_name': show.artist.name,
      'artist_image_link': show.artist.image_link,
      'start_time': show.start_time.strftime('%m/%d/%Y, %H:%M:%S')
    })
  return render_template('pages/shows.html', shows=data)

@app.route('/shows/create')
def create_shows():
  # renders form. do not touch.
  form = ShowForm()
  return render_template('forms/new_show.html', form=form)

@app.route('/shows/create', methods=['POST'])
def create_show_submission():
  # creating a new instance of Show as outlined in the sqlalchemy docs:
  # https://docs.sqlalchemy.org/en/14/orm/tutorial.html#create-an-instance-of-the-mapped-class
  #
  # try / except block based on the todo_app excercise from the tutorial

  error = False
  try:
    show = Show(
      artist_id = request.form['artist_id'],
      venue_id = request.form['venue_id'],
      start_time = request.form['start_time']
    )
    db.session.add(show)
    db.session.commit()
  except:
    error = True
    db.session.rollback()
    print(sys.exc_info())
  finally:
    db.session.close()
  if error:
    flash('An error occurred. Show could not be listed.')
    return render_template('pages/home.html')
  else:
    flash('Show was successfully listed!')
    return render_template('pages/home.html')

@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def server_error(error):
    return render_template('errors/500.html'), 500


if not app.debug:
    file_handler = FileHandler('error.log')
    file_handler.setFormatter(
        Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
    )
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info('errors')

#----------------------------------------------------------------------------#
# Launch.
#----------------------------------------------------------------------------#

# Default port:
if __name__ == '__main__':
    app.run()

# Or specify port manually:
'''
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
'''
