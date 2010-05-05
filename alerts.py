import settings
import models.data
from google.appengine.ext import db
from lib.prowlpy import Prowl
import logging

def ranking(pid, country, category_name, new_ranking):
	ranking_prowl(pid, country, category_name, new_ranking)

def ranking_prowl(pid, country, category_name, new_ranking):
	if hasattr(settings, "PROWL_RANKING_ALERTS"):
		if not settings.PROWL_RANKING_ALERTS.has_key(pid) or not settings.PROWL_RANKING_ALERTS[pid].has_key(country):
			return
		old_ranking = models.data.Ranking.all().filter("pid = ",pid).filter("country =", country).order("-date_created").get()
		if not old_ranking:
			return
		if old_ranking.ranking != new_ranking:
			for prowl_api_key in settings.PROWL_RANKING_ALERTS[pid][country]:
				p = Prowl(prowl_api_key)
				p.post("AppSales", event = "Ranking Changed", description = "%s is now ranked #%s in %s in %s" % (settings.PRODUCTS[pid]["name"], new_ranking, category_name, country))
