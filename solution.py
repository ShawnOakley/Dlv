import json
import urllib2
import tweepy
import re
import urlunshort
import httplib
import urlparse

# NOTE: 'uri' is used throughout to refer to 'urls' as a way to avoid inadvertant conflicts 
# with method names in any of the python modules

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

data = json.load(urllib2.urlopen('http://delvenews.com/api/matador/?email=shawnoakley@gmail.com'))
handle_list = data['twitter_handles']
start_date = data['begin_date']
end_date = data['end_date']

# Establishes minimum domain match count to label a comparison between handles as 'true'

min_count = 1

# Generates regex used to check for url in tweet text.
# Note the use of the capture group, which targets the top-level domain.
# By including this in the first regex used, and then calling <regex_return>.group(1)
# I could (ideally) avoid using the regex more than once per tweet.

http_regex = re.compile('http[s]?:\/\/([-A-Za-z0-9+&@#%?=~_()|!:,.;]*\.?[-A-Za-z0-9+&@#%?=~_()|!:,.;]*)\/?:?\w*\d*')

# Identifies whether a given tweet contains either a shortened url or a long url

def uri_tweet_identifier(regex, tweet_text):
	uri_search = re.search(regex, tweet_text)

	# The first 'if' test deals with urls that were truncated in the tweet's text
	# and are therefore un-openable or where no url is in the tweet's text

	if uri_search is None or len(uri_search.group()) < 12:
		return None
	else:
		return extract_domain(uri_search)

# Expands shortened url.  Does so by opening the actual shortened uri and seeing what
# the destination uri is  

def unshorten_uri(uri):
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

# Extracts a standard domain name from the url, irrespective of longer 
# pathnames or parameters  

def extract_domain(uri_text):
	# print 'URI Text'
	# print uri_text.group()
	expanded_uri_text = unshorten_uri(uri_text.group())
	expanded_uri_search = re.search(http_regex, expanded_uri_text)
	# print 'Full'
	# print expanded_uri_search.group()
	# print 'Domain'
	
	if expanded_uri_search is None:
		return None
	else:
		# print expanded_uri_search.group(1)
		return expanded_uri_search.group(1)	

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

# Compares domain counts between handles for a given domain, and adds to response_list for each handle
# if the counts are both above the given minimum
# Should be optimized to only compare once

for handle in handle_list:
	for handle2 in response_list[0][handle].keys():
		for domain in domain_count_dict[handle]:
			if domain in domain_count_dict[handle2].keys():
				if domain_count_dict[handle][domain] >= min_count and  domain_count_dict[handle2][domain] >= min_count:
					response_list[0][handle][handle2][domain] = True 
					response_list[0][handle2][handle][domain] = True 

# Removes blank values from key:value pairs

json_response = response_list[0].copy()
for handle in response_list[0].keys():
	json_response[handle] = {k:v for k, v in response_list[0][handle].iteritems() if v}

json_return = json.dumps([json_response], separators=(',',':'))

print json_return