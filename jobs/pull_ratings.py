import logging
import wsgiref.handlers
from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import login_required
from google.appengine.api import urlfetch
from google.appengine.api.labs import taskqueue
import re
import string
import settings
import jobs.app_store_codes
import alerts
from processors.rating_persistor import persist_rating


def store_ratings(pid, store_id):
	user_agent = "iTunes/4.2 (Macintosh; U; PPC Mac OS X 10.2"
	#url = settings.PRODUCTS[pid]['url']
	url = "http://ax.itunes.apple.com/WebObjects/MZStore.woa/wa/customerReviews?displayable-kind=11&id=%s" % settings.PRODUCTS[pid]['app_id']
	headers = {
				'User-Agent': user_agent,
				'X-Apple-Store-Front': "%d-1,5" % store_id,
				'Cache-Control': 'max-age=0',
			}
	response = urlfetch.fetch(url=url,
							method=urlfetch.GET,
							deadline=10,
							headers=headers)
	html = response.content
	country = jobs.app_store_codes.COUNTRIES[int(store_id)]
	if html.find("ratings-histogram") == -1:
		return None

	def parse(html):
		stars, total_number_of_ratings = re.compile("rating.*?aria-label='(.*?) star.*?rating-count.>(.*?) Ratings", re.S).findall(html)[0]

		votes = re.compile("class=\"vote\" .*?aria-label='(.*?) stars?, (.*?) ratings").findall(html)
		return stars, total_number_of_ratings, votes
	ratings_html = re.compile("all versions:.*?rating-url", re.S).findall(html)[0]
	stars, total_number_of_ratings, votes = parse(ratings_html)
	args = (pid, country, stars, int(total_number_of_ratings), int(votes[0][1]), int(votes[1][1]), int(votes[2][1]), int(votes[3][1]), int(votes[4][1]))
	logging.info(args)
	alerts.ratings(*args)
	persist_rating(*args)

class RatingsJob(webapp.RequestHandler):
	def get(self):
		for pid in settings.PRODUCTS:
			self.fetch_ratings(pid)

	def fetch_ratings(self, pid):
		countries_per_task = 3
		count = 0
		store_ids_to_process = []

		countries = settings.PRODUCTS[pid]['countries'] if settings.PRODUCTS[pid].has_key('countries') else jobs.app_store_codes.COUNTRIES
		for store_id in countries:
			count += 1
			store_ids_to_process.append(store_id)
			if count % countries_per_task == 0 or count == len(countries):
				# Enqueue task and reset list
				taskqueue.add(url='/jobs/pull_ratings/worker',
								method='POST',
								params={
										'pid': pid,
										'store_ids': ','.join(map(str, store_ids_to_process)),
										})
				store_ids_to_process = []

class RatingsWorker(webapp.RequestHandler):
	def post(self):
		pid = self.request.get("pid")
		store_ids = self.request.get("store_ids", ",").split(",")
		for store_id in store_ids:
			store_ratings(pid, int(store_id))


def test():
	url = "http://itunes.apple.com/us/app/my-times/id368515340?mt=8"
	store_id = 143441
	store_ratings("jga-mytimes", store_id)


def main():
	application = webapp.WSGIApplication([('/jobs/pull_ratings', RatingsJob),
											('/jobs/pull_ratings/worker', RatingsWorker)], debug=True)
	wsgiref.handlers.CGIHandler().run(application)

if __name__ == "__main__": main()
