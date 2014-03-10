import json
import urllib2
import tweepy
import re
import urlunshort
import httplib
import urlparse

# Sets up tweepy for API calls to Twitter
# Saving the consumer secret and consumer key in this manner isn't ideal.
# However, as the API is a dummy app created for the purposes of this exercise,
# it doesn't present an issue in this case.

consumer_secret = 'aiHpPpC805ot3SZOxEKeys5BlfGROioGP1xrAMdt4'
consumer_key = 'QiaGY882NRG2nk1yK0WOJg'
auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
api = tweepy.API(auth)

# auth.set_access_token(access_key, access_secret)
# https://stackoverflow.com/questions/7714282/return-actual-tweets-in-tweepy
# EXAMPLE:
# for tweepy_object in api.user_timeline(id="twitter"):
# 	print tweepy_object.text

# Grabs test data from delve API and extracts relevant search/comparison parameters

data = json.load(urllib2.urlopen('http://delvenews.com/api/matador/'))
handle_list = data['twitter_handles']
start_date = data['begin_date']
end_date = data['end_date']

# Establishes minimum domain match count to label a comparison between handles as 'true'

min_count = data['match_criteria']

# Generates regex used to check for url in tweet text.
# Note the use of the capture group, which targets the top-level domain.
# By including this in the first regex used, and then calling <regex_return>.group(1)
# I can avoid using the regex more than once per tweet.

trunc_regex = re.compile('http[s]?:\/\/(.+\.){0,3}([A-Za-z0-9]*)\.(co|\w):?[0-9]*\/?\w*\d*')
full_regex = re.compile('http[s]?:\/\/(.+\.){0,3}([A-Za-z0-9]*)\.(com|net|co.uk|gov|ly|in|\w):?[0-9]*\/?\w*\d*')

# test_search = api.search(handle_list[2], since=start_date, until=end_date)

# NEXT STEP:  regex http identifier in tweet text 
# http://blog.codinghorror.com/the-problem-with-urls/
# http://www.regexguru.com/2008/11/detecting-urls-in-a-block-of-text/
def uri_tweet_identifier(regex, tweet_text):
	uri_search = re.search(full_regex, tweet_text)
	print 'tweet text'
	print tweet_text
	print 'URI search 1'
	print uri_search.group()
	if uri_search is None:
		uri_search = re.search(trunc_regex, tweet_text)
		print 'URI search 2'
		print uri_search.group()

	# The first 'if' test deals with urls that were truncated in the tweet's text
	# and are therefore un-openable or where no url is in the tweet's text


	if uri_search is None or len(uri_search.group()) < 13:
		return None
	else:
		# Domain extraction call should go here.  Return extracted domain.
		# Expander is nested in extractor
		return extract_domain(uri_search)

# Checking for short URLs
# https://stackoverflow.com/questions/9557116/regex-php-code-to-check-if-a-url-is-a-short-url

# https://stackoverflow.com/questions/4201062/how-can-i-unshorten-a-url-using-python

def unshorten_uri(uri):
	# print 'URI: '
	# print uri
	parsed = urlparse.urlparse(uri)
	h = httplib.HTTPConnection(parsed.netloc)
	h.request('HEAD', parsed.path)
	response = h.getresponse()
	if response.status/100 == 3 and response.getheader('Location'):
		try:
			resp = urllib2.urlopen(response.getheader('Location'))
			return resp.url
		except:
			return response.getheader('Location')
	else:
		return uri

def extract_domain(uri_text):
	print 'URI Text'
	print uri_text.group()
	expanded_uri_text = unshorten_uri(uri_text.group())
	expanded_uri_search = re.search(full_regex, expanded_uri_text)
	print 'Full'
	print expanded_uri_search.group()
	print 'Domain'
	
	if expanded_uri_search is None:
		return None
	else:
		print expanded_uri_search.groups()
		# per the domain structure listed in the problem description, this return reconstructs
		# the uri proper format.
		# E.g.,  'http://boss.blogs.nytimes.com/2014/' becomes 'nytimes.com'
		return expanded_uri_search.groups[-2] + '.' + expanded_uri_search.groups[-1]

	# return urlunshort.is_shortened(uri_text.group())
	# return unshorten_uri(uri_text.group())
	
# for status in test_search:
# 	print "Tweet:"
# 	print status.text
# 	print uri_tweet_identifier(http_regex, status.text)
# 	print ''

# print 'Basic check on is_shortened:'
# print urlunshort.is_shortened("http://bit.ly/qlKaI")

# Use tweety's api date search functionality to create a dict mapping handle to tweets

tweet_dict = {handle: [returned_tweet.text for returned_tweet in api.search(handle, since=start_date, until=end_date)] for handle in handle_list}

# Generates dict and list to keep track of domain count and comparisons b/t handles, respectively

domain_count_dict = {handle: {} for handle in handle_list}

for handle in handle_list:
	for tweet in tweet_dict[handle]:
		domain = uri_tweet_identifier(http_regex, tweet)
		if domain is not None: 
			if not domain in domain_count_dict[handle].keys():
				domain_count_dict[handle][domain] = 1
			else:
				domain_count_dict[handle][domain] += 1


response_list = [{handle: {handle2: {} for handle2 in handle_list if handle2 != handle} for handle in handle_list}]

# Should be optimized to only compare once

# print domain_count_dict
# print ''
# print ''
# print response_list

for handle in handle_list:
	for handle2 in response_list[0][handle].keys():
		for domain in domain_count_dict[handle]:
			if domain in domain_count_dict[handle2].keys():
				if domain_count_dict[handle][domain] >= min_count and  domain_count_dict[handle2][domain] >= min_count:
					response_list[0][handle][handle2][domain] = True 
					response_list[0][handle2][handle][domain] = True 


# print 'Domain Count Array'
# print domain_count_dict

# print 'Response Array'
# print response_list[0]['DanielMorain']

print ''
print ''
print response_list