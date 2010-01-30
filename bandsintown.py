import cjson
import httplib
import re
import urllib


_conn = httplib.HTTPConnection("api.bandsintown.com")
app_id = None

# Helper stuff
def get_args():
	if app_id is None:
		raise InputException("app_id needs to be set!!")
	return [("format", "json"), ("app_id", app_id)]

slashes_re = re.compile('\\\/')
def clean_slashes_for_cjson(data):
	return slashes_re.sub('/', data)

def send_request(url, args = []):
	_conn.request("GET", "%s?%s" % (url, urllib.urlencode(args + get_args())))
	req = _conn.getresponse()
	if req.status != 200:
		raise RequestException("Request fail: %s" % req.read())

	return cjson.decode(clean_slashes_for_cjson(req.read()))

class InputException(Exception):
	pass

class RequestException(Exception):
	pass


class Artist(object):
	"""
	Contains information about one artists. Also methods for getting
	information about one artist or all events for an artist
	"""
	def __init__(self, name, url, mbid, upcomming_event_count):
		self.name = name
		self.url = url
		self.mbid = mbid
		self.upcomming_event_count = upcomming_event_count

	def __repr__(self):
		return repr({'name': self.name, 'url': self.url, 'mbid': self.mbid, 'upcomming_event_count': self.upcomming_event_count})

	def __str__(self):
		return "%s (%s)" % (self.name, self.mbid)

	@classmethod
	def _send_request(cls, url, mbid=None, name=None):
		if not mbid and not name or mbid and name:
		  raise InputException("Just one of mbid and name can be set")

		if mbid:
			name = "mbid_%s" % mbid

		return send_request(url % name)

	@classmethod
	def parse(cls, data):
		return Artist(data.get('name'), data.get('url'), data.get('mbid'), data.get('upcoming_events_count'))		

	@classmethod
	def events(cls, mbid=None, name=None):
		"""
		Get all events for one artist using either name or mbid
		"""
		data = Artist._send_request("/artists/%s/events", mbid, name)
		return Event.parse_all(data)

	@classmethod
	def get(cls, mbid=None, name=None):
		"""
		Get information about the artist using either name or mbid
		"""
		data = Artist._send_request("/artists/%s", mbid, name)
		return Artist.parse(data)

class Event(object):

	def __init__(self, id, url, ticket_url, ticket_status, datetime, on_date_datetime, artists, venue, status):
		self.id = id
		self.url = url
		self.ticket_url = ticket_url
		self.ticket_status = ticket_status
		self.datetime = datetime
		self.on_date_datetime = on_date_datetime
		self.artists = artists
		self.venue = venue
		self.status = status

	def __repr__(self):
		return repr({'id': self.id, 'url': self.url, 'ticket_url': self.ticket_url, 'ticket_status': self.ticket_status, 'datetime': self.datetime, 'on_date_datetime': self.on_date_datetime, 'artists': self.artists, 'venue': self.venue})

	def __str__(self):
		return "%s (%d)" % (self.url, self.id)

	@classmethod
	def parse_all(cls, data):
		events = []
		for event in data:
			events.append(Event.parse(event))

		return events

	@classmethod
	def parse(cls, data):
		artists = [Artist.parse(d) for d in data.get("artists", [])]
		venue = Venue.parse(data.get('venue', {}))
		return Event(data.get('id'), data.get('url'), data.get('ticket_url'), data.get('ticket_status'), data.get('datetime'), data.get('on_date_datetime'), artists, venue, data.get('status'))

	@classmethod
	def generate_args(cls, mbids=None, artists=None, location=None, radius=None, date='upcoming', page=None, per_page=None):
		if len(mbids or []) + len(artists or []) > 50:
			raise InputException("Maximum 50 artists (mbids + artist names)")
		if radius > 150:
			raise InputException("Maximum radius is 150")
		if per_page > 100:
			raise InputException("Maximum 100 per page")
		qs = []
		if mbids:
			for m in mbids:
				qs.append(('artists[]', 'mbid_%s' % m))
		if artists:
			for a in artists:
				qs.append(('artists[]', a))
		if location:
			qs.append(('location', location))
		if radius:
			qs.append(('radius', radius))
		if date:
			qs.append(('date', date))
		if page > 0:
			qs.append(('page', page))
		if per_page > 0:
			qs.append(('per_page', per_page))
		return qs		

	@classmethod
	def search(cls, mbids=[], artists=[], location=None, radius=None, date=None, page=None, per_page=None):
		"""
		Search for events using mbids, name of artists or location
		"""
		if not (artists or mbids) and not location:
			raise InputException("Must set either one artist or a location")

		qs = Event.generate_args(mbids, artists, location, radius, date, page, per_page)
		return Event.parse_all(send_request("/events/search", qs))

	@classmethod
	def recommended(cls, mbids=[], artists=[], location=None, radius=None, date=None, only_recs=None, page=None, per_page=None):
		"""
		Find recommended events using mbids, name of artists and location
		"""
		if not (artists or mbids) or not location:
			raise InputException("Must set both one artist and a location")

		qs = Event.generate_args(mbids, artists, location, radius, date, page, per_page)
		if only_recs is not None:
			qs.append(('only_recs', only_recs and 'true' or 'false'))

		return Event.parse_all(send_request("/events/recommended", qs))

	@classmethod
	def daily(cls):
		return Event.parse_all(send_request("/events/daily"))

class Venue(object):
	def __init__(self, id, name, city, region, country, url, latitude, longitude):
		self.id = id
		self.name = name
		self.city = city
		self.region = region
		self.country = country
		self.url = url
		self.latitude = latitude
		self.longitude = longitude

	def __repr__(self):
		return repr({'id': self.id, 'name': self.name, 'city': self.city, 'region': self.region, 'country': self.country, 'url': self.url, 'latitude': self.latitude, 'longitude': self.longitude})

	def __str__(self):
		return "%s (%d)" % (self.name, self.id)

	@classmethod
	def parse(cls, data):
		return Venue(data.get('id'), data.get('name'), data.get('city'), data.get('region'), data.get('country'), data.get('url'), data.get('latitude'), data.get('longitude'))
