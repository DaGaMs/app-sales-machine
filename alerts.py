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
		old_ranking = models.data.Ranking.all().filter("pid = ",pid).filter("country =", country).filter("category = ", category_name).order("-date_created").get()
		if not old_ranking:
			return
		if old_ranking.ranking != new_ranking:
			for prowl_api_key in settings.PROWL_RANKING_ALERTS[pid][country]:
				p = Prowl(prowl_api_key)
				p.post("AppSales", event = "Ranking Changed", description = "%s moved from #%s to #%s in %s in %s" % (settings.PRODUCTS[pid]["name"], old_ranking.ranking, new_ranking, category_name, country))


def ratings(pid, country, stars, count, five_star_count, four_star_count, three_star_count, two_star_count, one_star_count):
	if hasattr(settings, "PROWL_RATING_ALERTS"):
		if not settings.PROWL_RATING_ALERTS.has_key(pid) or not settings.PROWL_RATING_ALERTS[pid].has_key(country):
			return
		old_rating = models.data.Rating.get_current(pid, country)
		if not old_rating:
			return
		if old_rating.total_ratings != count:
			changes = []
			text = "%(count)s (%(diff)s)"
			if old_rating.five_star_count != five_star_count:
				changes.append(text % { 'count': 5, 'diff': old_rating.five_star_count - five_star_count })
			if old_rating.four_star_count != four_star_count:
				changes.append(text % { 'count': 4, 'diff': old_rating.four_star_count - four_star_count })
			if old_rating.three_star_count != three_star_count:
				changes.append(text % { 'count': 3, 'diff': old_rating.three_star_count - three_star_count })
			if old_rating.two_star_count != two_star_count:
				changes.append(text % { 'count': 2, 'diff': old_rating.two_star_count - two_star_count })
			if old_rating.one_star_count != one_star_count:
				changes.append(text % { 'count': 1, 'diff': old_rating.one_star_count - one_star_count })
			for prowl_api_key in settings.PROWL_RATING_ALERTS[pid][country]:
				p = Prowl(prowl_api_key)
				p.post("AppSales", event = "Rating Changed", description = \
						"%(name)s ratings have changed to %(stars)s stars (%(count)s).  [%(diffs)s]" %
						{ 'name': settings.PRODUCTS[pid]["name"], "stars": stars, "count": count, "diffs": ' '.join(changes) })
