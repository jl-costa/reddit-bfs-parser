## Introduction

A [breadth-first search](https://en.wikipedia.org/wiki/Breadth-first_search) bot that will crawl Reddit by finding internal hyperlinks (in /r/XXXXX/ format) in comments, and will build a directed network graph as it visits new subreddits.

It makes use of Pushshift.io's Reddit database. Due credit goes to [/u/Stuck_In_the_Matrix](https://www.reddit.com/user/Stuck_In_the_Matrix) for putting together and maintaining the Pushshift database.

For more information on the database and its API, please refer to:

[https://www.reddit.com/r/pushshift/comments/5gawot/pushshift_reddit_api_v20_documentation_use_this/](https://www.reddit.com/r/pushshift/comments/5gawot/pushshift_reddit_api_v20_documentation_use_this/)

This was originally coded for a network analysis project. The resulting graphs were analyzed with the Networkx package and visualized with Gephi. Many interesting things can be analyzed with a large-scale Reddit network. Some academic literature of relevance:

Olson, R. S., & Neal, Z. P. (2015). Navigating the massive world of reddit: using backbone networks to map user interests in social media. PeerJ Computer Science, 1–13. [https://doi.org/10.7717/peerj-cs.4](https://doi.org/10.7717/peerj-cs.4)

Newell, E., Jurgens, D., Saleem, H. M., Vala, H., Sassine, J., Armstrong, C., & Ruths, D. (2016). User Migration in Online Social Networks: A Case Study on Reddit During a Period of Community Unrest. Aaai, (Icwsm), 279–288.

Please use with care and read the cautionary notes below.

## Setup instructions

In an effort to make the sampling random, the bot starts with one randomly-generated node (subreddit). This random node is returned by Reddit's API, through the Praw wrapper. You will need a Reddit account with an API-registered application to fill out this section:

```python
# Replace #### with your creds
reddit = praw.Reddit(client_id='####',
		     client_secret='####',
		     password='####',
		     user_agent='Network bot by /u/####',
		     username='####')

# Verify connection to API:
print('successfully connected to Reddit API with user: ', reddit.user.me())
```
You will also want to modify the following fields to match your time period of interest. Please enter your minimum and maximum timestamps in UNIX time format:

```python
min_utc = 1425168000
max_utc = 1427846400
```

## Caution

As presented here, the bot is not configured to stop until the queue is empty. In a large-scale, small-world network like Reddit, what this means in practice is that unless your first node is an isolate, you will eventually crawl hundreds of thousands of nodes. This would obviously be very costly to implement.

I highly recommend you add some sort of threshold for the bot to stop. In my original project, I calculated the shortest path length between the origin node and the node being parsed in a given iteration, and configured the bot to stop once a shortest path length of X or more had been reached.

Example:

```python
# To be placed under the main while loop

shortest_path = nx.shortest_path_length(network, origin_node, node)

# Stop at depth of 5
if shortest_path <= 5:
  # Process node
else:
  continue
```
