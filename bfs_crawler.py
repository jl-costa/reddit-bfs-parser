# Initial imports and setup

import pandas as pd
from pandas.io.json import json_normalize
import numpy as np
from collections import deque
import praw
import networkx as nx
import urllib.request
import json
import re
import time

# API setup
# Replace #### with your creds
reddit = praw.Reddit(client_id='####',
		     client_secret='####',
		     password='####',
		     user_agent='Network bot by /u/####',
		     username='####')

# Verify connection to API:
print('successfully connected to Reddit API with user: ', reddit.user.me())

# Minimum and maximum posted times for fetched comments (in this case, March 2015)
min_utc = 1425168000
max_utc = 1427846400

# Temp dataframe for processing each node
comments_df = pd.DataFrame()

# Directed networkx graph
network = nx.DiGraph()

# Regex pattern for finding links to other subreddits in fetched comments
url_re = re.compile(pattern='\/r\/(?P<subname>\w{1,21})')

# Regex pattern for finding the UTC of the next page to be parsed
next_utc_re = re.compile('after=(?P<next_utc>\d+)')


# Functions

def commentParser(url):
	""" Connect to PushShift, fetch JSON multi-array, decode, and return
		as a Pandas DF object.
		:param url: PushShift.io API URL
		:return: Parsed comments and metadata or None
	"""
	response = urllib.request.urlopen(url)
	response_text = response.read().decode('utf-8')
	response_text = json.loads(response_text)
	if response_text['data']:
		comments = json_normalize(response_text['data'])
		metadata = json_normalize(response_text['metadata'])
		return (comments, metadata)
	else:
		return None


def urlParser(comment, node):
	""" Take parsed comment and find hyperlinks to other subreddits (nodes).
		:param comment: str object with the content of one parsed comment
		:param node: str object with the name of the subreddit in which comment
		was parsed
		:return: str object with the parsed hyperlink (if any)
	"""
	match = re.search(url_re, comment)
	if match and match.group(1) != node:
		match = match.group(1).lower()
		return match


def matchFinder(df, node):
	""" Take DF with all comments and find matches for links to other
    	subreddits. Eliminate self-links.
		:param df: PD dataframe object with all parsed comments
		:param node: str object with name of the subreddit currently
		being analyzed
		:return PD dataframe with matches added in a new column
    	"""
	df['Match'] = df['body'].apply(lambda x: urlParser(x, node))
	df.dropna(inplace=True)
	df = df[df['Match'] != node]
	return df


def apiParser(node, min_utc, max_utc, comments_df):
	""" Parse all comments for a given subreddit within the given time period.
		:param node: str object with the name of the subreddit to parse
		:param min_utc: int object with POSIX value of minimum date of defined time period
		:param max_utc: int object with POSIX value of maximum date of defined time period
		:param comments_df: Pandas DF object for storing all parsed comments
		:return: PD dataframe object with all parsed comments appended to it
	"""
	url = "https://apiv2.pushshift.io/reddit/search/comment/?subreddit={sub}&after={min_d}".format(sub=node,
												       min_d=min_utc)
	# Execute commentParser to fetch first page of results for node
	parser_results = commentParser(url)

	if parser_results == None:
		# Return DF with no appended comments if nothing can be parsed for the given time period
		return comments_df

	else:
		# Fetch all other pages of results for node
		while 'next_page' in parser_results[1].columns:
			new_url = parser_results[1].loc[0, 'next_page']
			next_utc = int(re.search(next_utc_re, new_url).group(1))

			comments_df = comments_df.append(parser_results[0].loc[:,
									       ['author',
										'body',
										'created_utc',
										'id']], ignore_index=True)

			if next_utc >= max_utc:
				break
			else:
				parser_results = commentParser(new_url)
		return comments_df


def graphAdder(df, graph, node, queue):
	"""Count frequency of each link in results, and add weighted 
	edges to graph object.
		:param df: PD dataframe object with all parsed comments and matches
		:param graph: Networkx DiGraph() object
		:param node: str object with name of the subreddit currently
		being analyzed
		:param queue: queue object of the BFS crawler
		:return: graph object with new weighted edges and nodes
		:return: queue object with new nodes added
	"""
	# 'Internal' visited set to avoid double iteration of duplicate matches
	graph_visited = set()

	matches = df['Match'].values
	matches_grouped = df.groupby('Match')

	for match in np.nditer(matches, flags=['refs_ok']):

		dest_node = np.array_str(match)

		if dest_node in graph_visited:
			continue

		else:
			weight = np.array_str(matches_grouped.count().loc[dest_node, 'id'])

			graph.add_edge(node,
						   dest_node,
						   attr_dict={'weight': weight})

			graph_visited.add(dest_node)
			queue.append(dest_node)
			time.sleep(0.1)

	return graph, queue


# BFS crawling

# Randomly generated first node in the network
origin_node = str(reddit.subreddit('random')).lower()

# Set of visited nodes
visited = set()

# Queue
queue = deque()

# Iteration count
counter = 0

# Process first node

queue.append(origin_node)
network.add_node(origin_node)

# BFS execution

while queue:
	counter += 1

	# Retrieve new node to process
	node = queue.pop()
	# BFS execution

	# Don't process an already visited node
	if node in visited:
		continue

	else:
		visited.add(node)
		comments_df = apiParser(node, min_utc, max_utc, comments_df)

		# Process df to find links to other subreddits
		comments_df = matchFinder(comments_df, node)

		# Verify there are edges to be added to graph
		if len(comments_df) == 0:
			continue
		else:
			network, queue = graphAdder(comments_df, network, node, queue)

	time.sleep(0.1)

else:
	print('queue empty')

# Write network to disk
nx.write_graphml(network, 'network_{one}_{two}.graphml'.format(one=origin_node,
							       two=min_utc))
