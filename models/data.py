from google.appengine.ext import db
import pickle
import StringIO


class AbstractReport(db.Model):
	income_revenue = db.FloatProperty()
	income_units = db.IntegerProperty()
	refund_loss = db.FloatProperty()
	refund_units = db.FloatProperty()
	pid = db.StringProperty(multiline=False)
	report_date = db.DateTimeProperty()
	date_created = db.DateTimeProperty(auto_now_add=True)

	# Intended to store dictionaries, but can store any object
	# See: http://appengine-cookbook.appspot.com/recipe/how-to-put-any-python-object-in-a-datastore
	_revenue_by_currency = db.BlobProperty()
	def _set_revenue_by_currency(self, x):
		f = StringIO.StringIO()
		pickle.dump(x, f)
		self._revenue_by_currency = db.Blob(f.getvalue())

	revenue_by_currency = property(lambda self:pickle.load(StringIO.StringIO(self._revenue_by_currency)), _set_revenue_by_currency)

	_units_by_country = db.BlobProperty()
	def _set_units_by_country(self, x):
		f = StringIO.StringIO()
		pickle.dump(x, f)
		self._units_by_country = db.Blob(f.getvalue())

	units_by_country = property(lambda self:pickle.load(StringIO.StringIO(self._units_by_country)), _set_units_by_country)

	@classmethod
	def get_totals(cls, pid):
		query = cls.all().filter("pid = ", pid)
		data = { 'revenue': 0, 'units': 0 }
		for item in query:
			data['revenue'] += item.income_revenue
			data['units'] += item.income_units

		return data


class Sale(AbstractReport):
	pass

class Upgrade(AbstractReport):
	pass

class RankingGroup(db.Model):
	date_created = db.DateTimeProperty(auto_now_add=True)
	pid = db.StringProperty(multiline=False)

class Ranking(db.Model):
	date_created = db.DateTimeProperty(auto_now_add=True)
	pid = db.StringProperty(multiline=False)
	category = db.StringProperty(multiline=False)
	country = db.StringProperty(multiline=False)
	ranking = db.IntegerProperty()
	group = db.ReferenceProperty(RankingGroup)


class Rating(db.Model):
	date_created = db.DateTimeProperty(auto_now_add = True)
	pid = db.StringProperty(multiline=False)
	country = db.StringProperty(multiline=False)
	total_stars = db.StringProperty()
	total_ratings = db.IntegerProperty()
	five_star_count = db.IntegerProperty()
	four_star_count = db.IntegerProperty()
	three_star_count = db.IntegerProperty()
	two_star_count = db.IntegerProperty()
	one_star_count = db.IntegerProperty()

	def __str__(self):
		return "%s: %s %s (%s)" % (self.pid, self.country, self.total_stars, self.total_ratings)

	@classmethod
	def get_current(cls, pid, country):
		return cls.all().filter("pid =", pid).filter("country =", country).order("-date_created").get()
