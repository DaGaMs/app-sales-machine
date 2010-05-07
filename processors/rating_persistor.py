from google.appengine.ext import db
import models.data

def persist_rating(pid, country, total_stars, total_ratings, five, four, three, two, one):
	rating = models.data.Rating()
	rating.pid = pid
	rating.country = country
	rating.total_stars = total_stars
	rating.total_ratings = total_ratings
	rating.five_star_count = five
	rating.four_star_count = four
	rating.three_star_count = three
	rating.two_star_count = two
	rating.one_star_count = one
	return rating.put()
