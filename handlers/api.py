import wsgiref.handlers
from google.appengine.ext import webapp
from google.appengine.ext import db
from django.utils import simplejson
from chart import SalesChart
from google.appengine.api import memcache
import settings
import sys
sys.path.insert(0, settings.APP_ROOT_DIR + '/lib')
from graphy.backends import google_chart_api
import models.data
import logging
import datetime

class DailyReportHandler(webapp.RequestHandler):
	def get(self):
		pid = self.request.get("pid")
		type = self.request.get("type", "sales")
		if type == "sales":
			query = models.data.Sale.all()
		else:
			query = models.data.Upgrade.all()
		data = query.filter("pid = ", pid).order('-report_date').fetch(20)

		def sale_to_dict(sale):
			return {
				'revenue': "%.2f" % sale.income_revenue,
				'units': sale.income_units,
				'pid': sale.pid,
				'report_date': str(sale.report_date.date())
				}

		dict = [sale_to_dict(sale) for sale in data]
		self.response.out.write(simplejson.dumps(dict))

class TotalsReportHandler(webapp.RequestHandler):
	def get(self):
		pid = self.request.get('pid')
		type = self.request.get('type', 'sales')
		cache_key = "%s_total_%s" % (pid, type)
		totals = memcache.get(cache_key)
		if not totals:
			if type == "sales":
				totals = models.data.Sale.get_totals(pid)
			else:
				totals = models.data.Upgrade.get_totals(pid)
			totals['revenue'] = "%.2f" % totals['revenue']
			memcache.add(cache_key, totals, 60 * 60)

		self.response.out.write(simplejson.dumps(totals))

class CurrentRankingsHandler(webapp.RequestHandler):
	def get(self):
		pid = self.request.get("pid")

		ranking_group_query = db.Query(models.data.RankingGroup)
		ranking_group_query.order('-date_created')
		ranking_group_query.filter('pid =', pid)
		ranking_group = ranking_group_query.get()
		last_pull_date = datetime.date.today()
		rankings = []
		if ranking_group:
			ranking_query = db.Query(models.data.Ranking)
			ranking_query.filter('group =', ranking_group)
			last_pull_date = ranking_group.date_created
			# Look for rankings created within an hour range since the last pull
			for ranking in ranking_query:
				dict = {'country': ranking.country, 'category': ranking.category, 'ranking': ranking.ranking}
				rankings.append(dict)
			rankings = { 'last_update': str(last_pull_date),'rankings': sorted(rankings, key=lambda k: k['country']) }
			self.response.out.write(simplejson.dumps(rankings))


class ChartHandler(webapp.RequestHandler):
	def get(self):
		pid = self.request.get("pid")

		overall_chart_url, concentrated_chart_url = SalesChart().units_chart(pid)
		
		self.response.out.write(simplejson.dumps({ 'chart_url': overall_chart_url }))

class SparkLinesHandler(webapp.RequestHandler):
	def get(self):
		pid = self.request.get("pid")
		type = self.request.get("type", "sales")
		cache_key = "%s_sparklines_%s" % (pid, type)
		chart_url = memcache.get(cache_key)
		if not chart_url:
			if type == "sales":
				query = models.data.Sale.all()
			else:
				query = models.data.Upgrade.all()

			data = query.filter("pid = ", pid).order('report_date').fetch(7)
			chart_data = [item.income_units for item in data]
			logging.info(chart_data)
			chart = google_chart_api.Sparkline(chart_data)
			chart_url = chart.display.Url(30, 15)
			memcache.add(cache_key, chart_url, 60 * 60)
		self.response.out.write(simplejson.dumps({ 'chart_url': chart_url}))

class RatingsHandler(webapp.RequestHandler):
    def get(self):
        pid = self.request.get('pid')
        country = self.request.get('country', 'United States')
        rating = models.data.Rating.get_current(pid, country)
        if not rating:
            return
        rating_dict = {
            'date_created': str(rating.date_created),
            'pid': rating.pid,
            'country': rating.country,
            'total_stars': rating.total_stars,
            'total_ratings': rating.total_ratings,
            'five_star_count': rating.five_star_count,
            'four_star_count': rating.four_star_count,
            'three_star_count': rating.three_star_count,
            'two_star_count': rating.two_star_count,
            'one_star_count': rating.one_star_count,
        }
        self.response.out.write(simplejson.dumps(rating_dict))

def main():
	application = webapp.WSGIApplication([('/api/sales', DailyReportHandler),
								('/api/rankings', CurrentRankingsHandler),
								('/api/chart', ChartHandler),
								('/api/totals', TotalsReportHandler),
								('/api/sparklines', SparkLinesHandler),
								('/api/ratings', RatingsHandler),
							], debug=True)
	wsgiref.handlers.CGIHandler().run(application)

if __name__ == '__main__':
	main()
