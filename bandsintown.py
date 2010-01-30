import cjson
import httplib
import re
import urllib

_conn = httplib.HTTPConnection("api.bandsintown.com")
app_id = "musichackdaysthlmtesting"

def get_args():
	return [("format", "json"), ("app_id", app_id)]

slashes_re = re.compile('\\\/')
def clean_slashes_for_cjson(data):
	return slashes_re.sub('/', data)

def send_request(url, args = []):
	print "%s?%s" % (url, urllib.urlencode(args + get_args()))
	_conn.request("GET", "%s?%s" % (url, urllib.urlencode(args + get_args())))
	req = _conn.getresponse()
	if req.status != 200:
		raise Exception("Request fail: %s" % req.read())

	return cjson.decode(clean_slashes_for_cjson(req.read()))


class Artist(object):
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
		  raise Exception("Just one of mbid and name can be set")

		if mbid:
			name = "mbid_%s" % mbid

		return send_request(url % name)

	@classmethod
	def parse(cls, data):
		return Artist(data.get('name'), data.get('url'), data.get('mbid'), data.get('upcoming_events_count'))		

	@classmethod
	def events(cls, mbid=None, name=None):
		data = Artist._send_request("/artists/%s/events", mbid, name)
		return Event.parse_all(data)

	@classmethod
	def get(cls, mbid=None, name=None):
		data = Artist._send_request("/artists/%s", mbid, name)
		return Artist.parse(data)

class Event(object):

	def __init__(self, id, url, ticket_url, ticket_status, datetime, on_date_datetime, artists, venue):
		self.id = id
		self.url = url
		self.ticket_url = ticket_url
		self.ticket_status = ticket_status
		self.datetime = datetime
		self.on_date_datetime = on_date_datetime
		self.artists = artists
		self.venue = venue

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
		return Event(data.get('id'), data.get('url'), data.get('ticket_url'), data.get('ticket_status'), data.get('datetime'), data.get('on_date_datetime'), artists, venue)

	@classmethod
	def generate_args(cls, mbids=None, artists=None, location=None, radius=None, date='upcoming', page=None, per_page=None):
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
		if not (artists or mbids) and not location:
			raise Exception("Must set either one artist or a location")

		qs = Event.generate_args(mbids, artists, location, radius, date, page, per_page)
		return Event.parse_all(send_request("/events/search", qs))

	@classmethod
	def recommended(cls, mbids=[], artists=[], location=None, radius=None, date=None, only_recs=None, page=None, per_page=None):
		if not (artists or mbids) or not location:
			raise Exception("Must set both one artist and a location")

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

if __name__ == '__main__':
  pass
  #print Artist.get(mbid='65f4f0c5-ef9e-490c-aee3-909e7ae6b2ab')
  #print Artist.events(mbid='65f4f0c5-ef9e-490c-aee3-909e7ae6b2ab')[0]
  #print Event.daily()[0]
  #print Event.search(None, 'Stockholm')[0]
  events = Event.recommended(['65f4f0c5-ef9e-490c-aee3-909e7ae6b2ab'], None, 'Stockholm, Sweden')
  for e in events:
  	print e
  	for a in e.artists:
  		print a
  	print
