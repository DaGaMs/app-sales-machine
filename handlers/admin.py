from google.appengine.ext import db
from google.appengine.ext import webapp
from google.appengine.api import users
from google.appengine.ext.webapp import template
from google.appengine.ext.webapp.util import login_required
import os
import cgi
import tarfile
import settings
from processors import report_persister
from chart import SalesChart
import models
import datetime
import logging

PAGE_NAME = 'Admin'
TEMPLATE_PATH = os.path.join(settings.SETTINGS['template_path'], 'admin.html')

class RootHandler(webapp.RequestHandler):

	@login_required
	def get(self):
		template_values = {
			'company_name': settings.SETTINGS['company_name'],
			'page_name': PAGE_NAME,
			'file_upload_name': settings.SETTINGS['upload_form_name'],
			}

		self.response.out.write(template.render(TEMPLATE_PATH, template_values))


class UploadHandler(webapp.RequestHandler):

	def post(self):
		file_data = self.request.POST[settings.SETTINGS['upload_form_name']].file
		tarball = tarfile.open(fileobj=file_data)
		for tarinfo in tarball:
			if tarinfo.isreg():
				# Persist original report and then persist the parsed contents of it
				file_buffer = tarball.extractfile(tarinfo).read()
				report_persister.persist(tarinfo.name, file_buffer)
		tarball.close()

		filename = self.request.POST[settings.SETTINGS['upload_form_name']].filename
		template_values = {
			'file_name': filename,
			'company_name': settings.SETTINGS['company_name'],
			'page_name': PAGE_NAME,
			'file_upload_name': settings.SETTINGS['upload_form_name'],
			}

		self.response.out.write(template.render(TEMPLATE_PATH, template_values))

class ChartHandler(webapp.RequestHandler):
	@login_required
	def get(self):
		pid = self.request.get("pid", None)
		if not pid:
			return
		overall_chart_url, concentrated_chart_url = SalesChart().units_chart(pid)

		self.response.out.write("<img src='%s'/>" % overall_chart_url)

class RankingsHandler(webapp.RequestHandler):
	@login_required
	def get(self):
		pid = self.request.get("pid", None)
		if not pid:
			self.response.out.write("missing pid")
			return

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
			rankings = sorted(rankings, key=lambda k: k['country'])
		ranking_template = os.path.join(settings.SETTINGS['template_path'], 'rankings.html')

		template_values = {
			'company_name': settings.SETTINGS['company_name'],
			'page_name': 'Rankings for %s' % pid,
			'rankings': rankings,
			'last_checked': last_pull_date
		}
		self.response.out.write(template.render(ranking_template, template_values))

class iPhoneHandler(webapp.RequestHandler):
	@login_required
	def get(self):
		pid = settings.PRODUCTS.keys()[0]
		template_path = os.path.join(settings.SETTINGS['template_path'], 'iphone.html')
		self.response.out.write(template.render(template_path, { 'pid': pid }))

