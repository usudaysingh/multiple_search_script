#!/usr/bin/python
import requests
import grequests
import tweepy
import pickle
import threading
import json
from tweepy import OAuthHandler
# from oauth_hook import OAuthHook
from tweepy import API
from BaseHTTPServer import BaseHTTPRequestHandler,HTTPServer
import multiprocessing
from urlparse import urlparse
from multiprocessing.dummy import Pool as ThreadPool 

PORT_NUMBER = 8080

#This class will handles any incoming request from
#the browser 
class myHandler(BaseHTTPRequestHandler):

	def get_query(self):
		try:
			query = urlparse(self.path).query
			query = query.split('=')[1]
			return query
		except:
			return None

	def parallel_request(self,url):
		CONSUMER_KEY = "oinVCsbl9qeXdNAQG3Uut5YOC"
		CONSUMER_SECRET = "aegQKNZkyVf7UP20v24QQNVKBXnZXCSPCuHSKGafuXBwGvZGAg"
		if url == 'twitter':
			auth = OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET)
			api = API(auth, timeout=1)
			response = api.search(q=self.get_query(), count=10, result_type='recent')
		else:
			try:
				response = requests.get(url,timeout=1)
			except requests.exceptions.Timeout:
				response = {'result': None, 'message': 'Request timed out', 'query': query}
			except requests.RequestException:
				response = {'result': None, 'message': "%s - %s" % (repr(e), e.__doc__), 'query': query}
		return response

	def format_data(self, query):
		total_urls = [
			'http://api.duckduckgo.com/?q='+query+'&format=json',
			'https://www.googleapis.com/customsearch/v1?key=AIzaSyBQcWOC2mlTkrFRnCTn_8hsREevDdT37yU&cx=010599593370841992410:btffvk1h6ge&q='+query,
			'twitter'
		]
		pool = ThreadPool(3)
		results = pool.map(self.parallel_request, total_urls)
		pool.close() 
		pool.join()
		try:
			duckduckgo_result = [{'url':data.get('FirstURL','Not Defined'), 'text':data.get('Text','Not Defined')} for data in results[0].json().get('RelatedTopics')]
		except:
			duckduckgo_result = results[0].json()

		try:
			google_result = [{'url':data.get('formattedUrl','Not Defined'), 'text':data.get('title','Not Defined')} for data in results[1].json().get('items')]
		except:
			google_result = results[1].json()

		try:
			twitter_result = [{'url':data.source_url,'text':data.text} for data in results[2]]
		except:
			twitter_result = results[2].json()
		final_result = {
			'query':query,
			'results':{
				'google':google_result,
				'duck':duckduckgo_result,
				'twitter':twitter_result
			}
		}

		return final_result

	def do_GET(self):
		query = self.get_query()

		if query:
			final_result = self.format_data(query)
		else:
			final_result = {'error':'Please enter query'}

		self.send_response(200)
		self.send_header('Content-type','application/json')
		self.end_headers()
		self.wfile.write(json.dumps(final_result))
		return 

try:
	server = HTTPServer(('', PORT_NUMBER), myHandler)
	print 'Started httpserver on port ' , PORT_NUMBER
	server.serve_forever()

except KeyboardInterrupt:
	print '^C received, shutting down the web server'
	server.socket.close()
