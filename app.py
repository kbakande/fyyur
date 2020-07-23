#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

import json
import dateutil.parser
import babel
from flask import Flask, render_template, request, Response, flash, redirect, jsonify, url_for
from flask_moment import Moment
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy import or_
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from forms import *
from customValidator import flash_errors
import sys
from datetime import datetime
#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')
db = SQLAlchemy(app)

# TODO: connect to a local postgresql database
migrate = Migrate(app, db)

#----------------------------------------------------------------------------#
# Models.
#----------------------------------------------------------------------------#

class Venue(db.Model):
    __tablename__ = 'venues'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    address = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))

    # TODO: implement any missing fields, as a database migration using Flask-Migrate
    genres = db.Column(ARRAY(db.String(120)))
    website_link = db.Column(db.String(120))
    seeking_talent = db.Column(db.Boolean)
    seeking_description = db.Column(db.String(500))
    shows = db.relationship('Show', backref= db.backref('venue', lazy=True))

class Artist(db.Model):
    __tablename__ = 'artists'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    genres = db.Column(ARRAY(db.String(120)))
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))

    # TODO: implement any missing fields, as a database migration using Flask-Migrate
    website_link = db.Column(db.String(120))
    seeking_venue = db.Column(db.Boolean)
    seeking_description = db.Column(db.String(500))
    shows = db.relationship('Show', backref = db.backref('artist', lazy=True))


# TODO Implement Show and Artist models, and complete all model relationships and properties, as a database migration.
class Show(db.Model):
  __tablename__= 'shows'

  id = db.Column(db.Integer, primary_key=True)
  artist_id = db.Column(db.Integer, db.ForeignKey('artists.id'), nullable=False)
  venue_id = db.Column(db.Integer, db.ForeignKey('venues.id'), nullable=False)
  start_time = db.Column(db.DateTime, nullable=False)


#----------------------------------------------------------------------------#
# Filters.
#----------------------------------------------------------------------------#

def format_datetime(value, format='medium'):
  date = dateutil.parser.parse(value)
  if format == 'full':
      format="EEEE MMMM, d, y 'at' h:mma"
  elif format == 'medium':
      format="EE MM, dd, y h:mma"
  return babel.dates.format_datetime(date, format)

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
  data = []
  uniqueAreas =  db.session.query(Venue.city, Venue.state).group_by(Venue.city, Venue.state).all()
  for area in uniqueAreas:
    venueTemp = []
    venueInArea = Venue.query.filter_by(state=area[1]).filter_by(city=area[0]).all()
    for venue in venueInArea:
      upcomingShow = 0
      for show in venue.shows:
        if show.start_time > datetime.now():
          upcomingShow +=1
      venueTemp.append({"id": venue.id, "name": venue.name, "num_upcoming_shows": upcomingShow})
    data.append({"city": area[0], "state": area[1], "venues": venueTemp})
  return render_template('pages/venues.html', areas=data);

@app.route('/venues/search', methods=['POST'])
def search_venues():
  # case insensitive search of venues using city, state and name
  searchTerm = request.form.get("search_term", "")
  searchTerm = "%{}%".format(searchTerm)
  searchVenues = Venue.query.filter( or_(Venue.name.ilike(searchTerm), Venue.city.ilike(searchTerm), Venue.state.ilike(searchTerm))).all()
  searchVenueCount = len(searchVenues)
  data = []
  for searchVenue in searchVenues:
    upcomingShow = 0
    for show in searchVenue.shows:
      if show.start_time > datetime.now():
        upcomingShow +=1
    data.append({"id": searchVenue.id, "name": searchVenue.name, "num_upcoming_shows": upcomingShow })

  response = {
    "count": searchVenueCount,
    "data": data
  }
  return render_template('pages/search_venues.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
  # shows the venue page with the given venue_id
  venueWithID = Venue.query.get(venue_id)
  pastShows, pastShowCount, upcomingShows, upcomingShowCount = [], 0, [], 0
  for show in venueWithID.shows:
    if show.start_time > datetime.now():
      showArtist = Artist.query.get(show.artist_id)
      upcomingShows.append({"artist_id": showArtist.id, "artist_name": showArtist.name, "start_time": str(show.start_time)})
      upcomingShowCount +=1
    else:
      showArtist = Artist.query.get(show.artist_id)
      pastShows.append({"artist_id": showArtist.id, "artist_name": showArtist.name, "start_time": str(show.start_time)})
      pastShowCount +=1
    pastShows, pastShowCount, upcomingShows, upcomingShowCount = [], 0, [], 0
  venueGenres = str(''.join(venueWithID.genres)).strip('\{\}').split(",")
  data = {
    "id": venueWithID.id,
    "name": venueWithID.name,
    "genres": venueGenres,
    "address": venueWithID.address,
    "city": venueWithID.city,
    "state": venueWithID.state,
    "phone": venueWithID.phone,
    "facebook_link": venueWithID.facebook_link,
    "website_link": venueWithID.website_link,
    "image_link": venueWithID.image_link,
    "seeking_talent": venueWithID.seeking_talent,
    "past_shows": pastShows,
    "upcoming_shows": upcomingShows,
    "past_shows_count": pastShowCount,
    "upcoming_shows_count": upcomingShowCount,
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
  # called upon submitting the new venue listing form
  form = VenueForm()
  error = False
  if form.validate_on_submit():
    try:
      venueExist = Venue.query.filter_by(name=request.form['name']).scalar()
      if venueExist:
        pass
      else:
        if request.form.get("seeking_talent") == 'y':
          seeking_talent = True
        else:
          seeking_talent = False  
        venue = Venue(
        name = request.form['name'],
        city = request.form['city'],
        state = request.form['state'],
        address = request.form['address'],
        phone = request.form['phone'],
        facebook_link = request.form['facebook_link'],
        genres = request.form.getlist("genres"),
        website_link = request.form['website_link'],
        image_link = request.form['image_link'],
        seeking_talent = seeking_talent,
        )
        db.session.add(venue)
        db.session.commit()
        data = Venue.query.all()[-1]
    except:
      error =  True
      db.session.rollback()
      print(sys.exc_info())
    finally:
      if venueExist:
        flash('Venue with name: \" ' + request.form['name'] + '\" already exists.')
        return render_template('forms/new_venue.html', form=form)
      elif error:
        db.session.close()
        flash('An error occurred. Venue ' + request.form['name'] + ' could not be listed.')
        return render_template('forms/new_venue.html', form=form)
      else:
        db.session.close()
        flash('Venue ' + data.name + ' was successfully listed!')
        return render_template('pages/home.html')
  else:
      flash_errors(form)
      return render_template('forms/new_venue.html', form=form)

@app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
  try:
    venueWithID = Venue.query.get(venue_id)
    for show in venueWithID.shows:
      db.session.delete(show)
    
    db.session.delete(venueWithID)
    db.session.commit()
  except:
    db.session.rollback()
    print(sys.exc_info())
  finally:
    db.session.close()
    return jsonify({'success': True})

#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():
  artists = Artist.query.all()
  data = []
  for artist in artists:
    data.append({"id": artist.id, "name": artist.name})
  return render_template('pages/artists.html', artists=data)

@app.route('/artists/search', methods=['POST'])
def search_artists():
  # case-insensearch 
  searchTerm = request.form.get("search_term", "")
  searchTerm = "%{}%".format(searchTerm)
  searchArtists = Artist.query.filter(or_(Artist.name.ilike(searchTerm), Artist.city.ilike(searchTerm), Artist.state.ilike(searchTerm))).all()
  searchArtistCount = len(searchArtists)
  data = []
  upcoming_shows = 0
  for searchArtist in searchArtists:
    for show in searchArtist.shows:
      if show.start_time > datetime.now():
        upcoming_shows += 1
    upcoming_shows = 0
    data.append({"id": searchArtist.id, "name": searchArtist.name, "num_upcoming_shows": upcoming_shows})

  response={
    "count": searchArtistCount,
    "data": data,
  }
  return render_template('pages/search_artists.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
  artistWithID = Artist.query.get(artist_id)
  pastShows, pastShowCount, upcomingShows, upcomingShowCount = [], 0, [], 0
  for show in artistWithID.shows:
    if show.start_time > datetime.now():
      showVenue = Venue.query.get(show.venue_id)
      upcomingShows.append({"venue_id": showVenue.id, "venue_name": showVenue.name, "start_time": str(show.start_time)})
      upcomingShowCount +=1
    else:
      showVenue = Venue.query.get(show.venue_id)
      pastShows.append({"venue_id": showVenue.id, "venue_name": showVenue.name, "start_time": str(show.start_time)})
      pastShowCount +=1
    pastShows, pastShowCount, upcomingShows, upcomingShowCount = [], 0, [], 0
  artistGenres = str(''.join(artistWithID.genres)).strip('\{\}').split(",")
  data = {
    "id": artistWithID.id,
    "name": artistWithID.name,
    "genres": artistGenres,
    "city": artistWithID.city,
    "state": artistWithID.state,
    "phone": artistWithID.phone,
    "facebook_link": artistWithID.facebook_link,
    "website_link": artistWithID.website_link,
    "image_link": artistWithID.image_link,
    "seeking_venue": artistWithID.seeking_venue,
    "past_shows": pastShows,
    "upcoming_shows": upcomingShows,
    "past_shows_count": pastShowCount,
    "upcoming_shows_count": upcomingShowCount,
  }
  return render_template('pages/show_artist.html', artist=data)

#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
 artist = Artist.query.get(artist_id)
 form = ArtistForm(obj = artist)
 return render_template('forms/edit_artist.html', form=form, artist=artist)  

@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
  form = ArtistForm()
  error = False
  existArtist = Artist.query.get(artist_id)
  if form.validate_on_submit():
    try:
      existArtist.name = request.form.get("name")
      existArtist.city = request.form.get("city")
      existArtist.state = request.form.get("state")
      existArtist.phone = request.form.get("phone")
      existArtist.genres= request.form.getlist("genres")
      existArtist.facebook_link = request.form.get("facebook_link")
      existArtist.website_link = request.form.get("website_link")
      existArtist.image_link = request.form.get("image_link")
      if request.form.get("seeking_venue") == 'y':
        existArtist.seeking_venue = True
      else:
        existArtist.seeking_venue = False
      db.session.commit()
    except:
      error = True
      db.session.rollback()
      print(sys.exc_info())
    finally:
      if error:
        flash('Artist  ' + existArtist.name + ' record is not edited')
        db.session.close()
        return render_template('forms/edit_artist.html', form=form, artist=existArtist) 
      else:
        flash('Artist  ' + existArtist.name + ' has been edited successfully')
        db.session.close()
        return redirect(url_for('show_artist', artist_id=artist_id))
  else:
      flash_errors(form)
      return render_template('forms/edit_artist.html', form=form, artist=existArtist) 

@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
  venue = Venue.query.get(venue_id)
  form = VenueForm(obj = venue)
  return render_template('forms/edit_venue.html', form=form, venue=venue)

@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
  form = VenueForm()
  error = False
  existVenue = Venue.query.get(venue_id)
  if form.validate_on_submit():
    try:
      existVenue.name = request.form.get("name")
      existVenue.city = request.form.get("city")
      existVenue.state = request.form.get("state")
      existVenue.address = request.form.get("address")
      existVenue.phone = request.form.get("phone")
      existVenue.genres= request.form.getlist("genres")
      existVenue.facebook_link = request.form.get("facebook_link")
      existVenue.website_link = request.form.get("website_link")
      existVenue.image_link = request.form.get("image_link")
      if request.form.get("seeking_talent") == 'y':
        existVenue.seeking_talent = True
      else:
        existVenue.seeking_talent = False
      db.session.commit()
    except:
      error = True
      db.session.rollback()
      print(sys.exc_info())
    finally:
      if error:
        flash('Venue ' + existVenue.name + ' record is not edited')
        db.session.close()
        return render_template('forms/edit_venue.html', form=form, venue=existVenue) 
      else:
        flash('Venue  ' + existVenue.name + ' has been edited successfully')
        db.session.close()
        return redirect(url_for('show_venue', venue_id=venue_id))
  else:
    flash_errors(form)
    return render_template('forms/edit_venue.html', form=form, venue=existVenue)


#  ----------------------------------------------------------------
#  Create Artist
#  ----------------------------------------------------------------

@app.route('/artists/create', methods=['GET'])
def create_artist_form():
  form = ArtistForm()
  return render_template('forms/new_artist.html', form=form)

@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
  # called upon submitting the new artist listing form
  form = ArtistForm()
  error = False
  if form.validate_on_submit():
    try:
      artistExist = Artist.query.filter_by(name=request.form['name']).scalar()
      if artistExist:
        pass
      else:
        if request.form.get("seeking_venue") == 'y':
          seeking_venue = True
        else:
          seeking_venue = False  
        artist = Artist(
        name = request.form['name'],
        city = request.form['city'],
        state = request.form['state'],
        phone = request.form['phone'],
        facebook_link = request.form['facebook_link'],
        genres = request.form.getlist("genres"),
        website_link = request.form['website_link'],
        image_link = request.form['image_link'],
        seeking_venue = seeking_venue,
        )
        db.session.add(artist)
        db.session.commit()
        data = Artist.query.all()[-1]
    except:
      error =  True
      db.session.rollback()
      print(sys.exc_info())
    finally:
      if artistExist:
        flash('Artist with name: \" ' + request.form['name'] + '\" already exists.')
        return render_template('forms/new_artist.html', form=form)
      elif error:
        db.session.close()
        flash('An error occurred. Artist ' + request.form['name'] + ' could not be listed.')
        return render_template('forms/new_artist.html', form=form)
      else:
        db.session.close()
        flash('Artist ' + data.name + ' was successfully listed!')
        return render_template('pages/home.html')
  else:
      flash_errors(form)
      return render_template('forms/new_artist.html', form=form)

@app.route('/artists/<artist_id>', methods=['DELETE'])
def delete_artist(artist_id):
  try:
    artistWithID = Artist.query.get(artist_id)
    for show in artistWithID.shows:
      db.session.delete(show)
    
    db.session.delete(artistWithID)
    db.session.commit()
  except:
    db.session.rollback()
    print(sys.exc_info())
  finally:
    db.session.close()
    return jsonify({'success': True})

#  ----------------------------------------------------------------
#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
  upcomingShows = Show.query.filter(Show.start_time > datetime.now()).all()
  data = []
  for show in upcomingShows:
    showVenue = Venue.query.get(show.venue_id)
    showArtist= Artist.query.get(show.artist_id)
    data.append({
    "venue_id": showVenue.id,
    "venue_name": showVenue.name,
    "artist_id":showArtist.id,
    "artist_name": showArtist.name,
    "artist_image_link": showArtist.image_link,
     "start_time": str(show.start_time)
    })
  return render_template('pages/shows.html', shows=data)

@app.route('/shows/create')
def create_shows():
  # renders form. do not touch.
  form = ShowForm()
  return render_template('forms/new_show.html', form=form)

@app.route('/shows/create', methods=['POST'])
def create_show_submission():
  form = ShowForm()
  if form.validate_on_submit():
    error = False
    try:
      artistid = Artist.query.filter_by(id=request.form['artist_id']).scalar()
      venueid = Venue.query.filter_by(id=request.form['venue_id']).scalar()
      if not venueid:
        pass
      elif not artistid:
        pass
      else:
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
      if not venueid:
        flash('Venue with ID ' + request.form['venue_id'] + ' does not exist.')
        return render_template('forms/new_show.html', form=form)
      elif not artistid:
        flash('Artist with ID ' + request.form['artist_id'] + ' does not exist.')
        return render_template('forms/new_show.html', form=form)
      elif error:
        db.session.close()
        flash('Show was not successfully listed!')
        return render_template('forms/new_show.html', form=form)
      else:
        flash('Show was successfully listed!')
        return render_template('pages/home.html')
  else:
    flash_errors(form)
    return render_template('forms/new_show.html', form=form)

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
