import wsgiref.handlers
from google.appengine.ext import webapp
from google.appengine.ext import db
from google.appengine.api import mail
from google.appengine.ext.webapp.util import login_required
from google.appengine.api.labs import taskqueue
from google.appengine.ext.webapp import template
import datetime
import string
import locale
import sys
import os

import logging
import settings
import models.data
from chart import SalesChart

class EmailReport(webapp.RequestHandler):

	def get(self):
		products = settings.PRODUCTS.keys()
		for pid in products:
			product_name = settings.PRODUCTS[pid]['name']
			sales_start = sales_end = upgrades_start = upgrades_end = upgrades_total = upgrade_rate = upgrade_base = last_reported_upgrades_total = 0

			# Start and end dates
			sales_query_asc = db.Query(models.data.Sale)
			sales_query_asc.filter('pid =', pid)
			sales_query_asc.order('report_date')
			last_reported_sales_total = 0
			if sales_query_asc.get() != None:
				sales_start = sales_query_asc.get().report_date
				sales_query_desc = db.Query(models.data.Sale)
				sales_query_desc.filter('pid =', pid)
				sales_query_desc.order('-report_date')
				sales_end = sales_query_desc.get().report_date

				# Last reported date downloads
				sales_query_desc.filter('report_date =', sales_end)
				last_reported_sales_total = self._total_income_units(sales_query_desc)

			# Total number of downloads
			sales_total = self._total_income_units(sales_query_asc)

			# Total sales income
			sales_total_revenue = 0
			for sale in sales_query_asc:
				sales_total_revenue += sale.income_revenue

			# Upgrades
			product_versions = settings.PRODUCTS[pid]['versions']
			if len(product_versions) > 1:
				upgrades_query = db.Query(models.data.Upgrade)
				upgrades_query.order('report_date')
				upgrades_query.filter('pid =', pid)
				upgrades_start = settings.PRODUCTS[pid]['versions'][-1]['date']
				upgrades_end = sales_end

				# Total number of upgrades
				upgrades_total = self._total_income_units(upgrades_query)

				# Last reported date upgrades
				upgrades_query.filter('report_date =', upgrades_end)
				last_reported_upgrades_total = self._total_income_units(upgrades_query)

				# Calculate upgrade rate from date of second release if there are only 2 releases
				if len(product_versions) == 2:
					sales_query_asc.filter('report_date <=', upgrades_start)
					upgrade_base = self._total_income_units(sales_query_asc)
					if upgrade_base == 0: upgrade_base = sales_total
				else:
					# There are more than two release so the best we can do is calculate an upgrade rate over all downloads
					upgrade_base = sales_total
					# Set upgrades start date to second release
					upgrades_start = settings.PRODUCTS[pid]['versions'][1]['date']

				if upgrade_base > 0:
					upgrade_rate = (1.0 * upgrades_total / upgrade_base) * 100
				else:
					upgrade_rate = 0

			# Rankings
			ranking_group_query = db.Query(models.data.RankingGroup)
			ranking_group_query.order('-date_created')
			ranking_group_query.filter('pid =', pid)
			ranking_group = ranking_group_query.get()
			last_pull_date = datetime.date.today()
			if ranking_group:
				ranking_query = db.Query(models.data.Ranking)
				ranking_query.filter('group =', ranking_group)
				rankings = []
				last_pull_date = ranking_group.date_created
				# Look for rankings created within an hour range since the last pull
				for ranking in ranking_query:
					dict = {'country': ranking.country, 'category': ranking.category, 'ranking': ranking.ranking}
					rankings.append(dict)
				rankings = sorted(rankings, key=lambda k: k['country'])
				logging.info(rankings)

			# Ratings
			countries = settings.PRODUCTS[pid]['countries'] if settings.PRODUCTS[pid].has_key('countries') else jobs.app_store_codes.COUNTRIES
			ratings = []
			for country_id, country in countries.items():
				latest_ratings = models.data.Rating.get_current(pid = pid, country = country)
				if latest_ratings:
					ratings.append(latest_ratings)

			overall_chart_url, concentrated_chart_url = SalesChart().units_chart(pid)
			product = {
					'name': product_name,
					'last_reported_sales_total': last_reported_sales_total,
					'last_reported_upgrades_total': last_reported_upgrades_total,
					'sales_start': self._date_string(sales_start),
					'sales_end': self._date_string(sales_end),
					'sales_total': self._format_number(sales_total),
					'sales_total_revenue': round(sales_total_revenue, 2),
					'upgrades_start': self._date_string(upgrades_start),
					'upgrades_end': self._date_string(upgrades_end),
					'upgrades_total': self._format_number(upgrades_total),
					'upgrade_rate': str(round(upgrade_rate, 2)) + '%',
					'upgrade_base': self._format_number(upgrade_base),
					'currency': settings.SETTINGS['base_currency'],
					'rankings_pull_date': last_pull_date,
					'rankings': rankings,
					'overall_chart_url': overall_chart_url,
					'concentrated_chart_url': concentrated_chart_url,
					'ratings': ratings,
					}

			path = os.path.join(settings.SETTINGS['template_path'], 'report.html')
			email_body = template.render(path, product)

			subject = '%s %s App Store report' % (datetime.date.today().strftime('%Y%m%d'), product['name'])
			send_email = self.request.get("email", "true")
			if send_email == "true":
				self.send_email(pid, subject, email_body)
			else:
				self.response.out.write(email_body)

	def _total_income_units(self, reports):
		total = 0
		for report in reports:
			total += report.income_units
		return total

	def _date_string(self, date):
		if date:
			return date.strftime('%Y-%m-%d')
		else:
			return 'Unavailable'

	def _format_number(self, number):
		locale.setlocale(locale.LC_ALL,"")
		return locale.format('%d', number, True)
	def send_email(self, pid, subject, email_body):
		if len(settings.PRODUCTS[pid]['to_addresses']) == 0:
			return
		message = mail.EmailMessage(sender=settings.SETTINGS['admin_email_address'],
									subject=subject)
		message.to = settings.PRODUCTS[pid]['to_addresses']
		message.html = email_body
		message.send()


def main():
	application = webapp.WSGIApplication([('/jobs/email_report', EmailReport)], debug=True)
	wsgiref.handlers.CGIHandler().run(application)

if __name__ == '__main__':
	main()
