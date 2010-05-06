import wsgiref.handlers
from google.appengine.ext import webapp
from google.appengine.ext import db
from django.utils import simplejson
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
		data = query.filter("pid = ", pid).order('-report_date').fetch(100)

		def sale_to_dict(sale):
			return {
				'revenue': sale.income_revenue,
				'units': sale.income_units,
				'pid': sale.pid,
				'report_date': str(sale.report_date.date())
				}

		dict = [sale_to_dict(sale) for sale in data]
		self.response.out.write(simplejson.dumps(dict))

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


def main():
	application = webapp.WSGIApplication([('/api/sales', DailyReportHandler),
								('/api/rankings', CurrentRankingsHandler),
							], debug=True)
	wsgiref.handlers.CGIHandler().run(application)

if __name__ == '__main__':
	main()
