from google.appengine.ext import db
import models.data
import logging

def persist_ranking_group(pid):
	group = models.data.RankingGroup()
	group.pid = pid
	return group.put()

def persist_ranking(pid, value, country, category, group_id):
	ranking = models.data.Ranking()
	ranking.pid = pid
	ranking.category = category
	ranking.country = country
	ranking.ranking = value
	ranking.group = models.data.RankingGroup.get_by_id(group_id)
	logging.info(group_id)
	logging.info(ranking.group)
	return ranking.put()
