import argparse
import re
import urllib.request
from html.parser import HTMLParser
import os
import json
import time
import traceback
import sys
from filter_data import filter_data

readen_post_ids = set()

def main():
	os.makedirs(OPTS.dataset_dir, exist_ok=True)

	readen_post_ids_file = os.path.join(OPTS.dataset_dir, 'readen_post_ids.txt')
	if os.path.exists(readen_post_ids_file):
		with open(readen_post_ids_file, 'r') as f:
			readen_post_ids.update(f.read().split('\n'))
			print('readen_post_ids', len(readen_post_ids))

	while True:
		try:
			threads = get_threads(OPTS.board)
			for thread_id in threads:
				process_thread(thread_id, OPTS.board, OPTS.dataset_dir)
		finally:
			with open(readen_post_ids_file, 'w') as f:
				f.write('\n'.join(readen_post_ids))

		print('pause...')
		time.sleep(1800)

def get_threads(board):
	json_str = request_json('https://2ch.hk/' + board + '/threads.json')
	threads = json.loads(json_str)
	thread_ids = list(map(
			lambda thread: str(thread['num']),
			threads['threads']))
	return thread_ids

def process_thread(thread_id, board, ds_dir):
	try:
		posts = get_thread_posts(board, thread_id)

		for post in posts:
			post.comment = filter_data(post.comment)
		posts = list(filter(
				lambda post: len(post.comment) > 1,
				posts))

		pairs = thread_posts_to_pairs(posts)

		pairs = list(filter(
				lambda pair: pair[1].id not in readen_post_ids,
				pairs))
		if len(pairs) == 0:
			return

		ids = [post.id for post in posts]
		readen_post_ids.update(ids)
		print('posts readen:', len(readen_post_ids))

		with open(
				os.path.join(ds_dir, thread_id + '.txt'),
				'ab') as f:
			comments = [pair[0].comment + '\n\n' + pair[1].comment for pair in pairs]
			comments = '\n\n'.join(comments) + '\n\n'
			f.write(comments.encode('utf-8'))
			print(comments)
	except KeyboardInterrupt:
		raise
	except:
		print(traceback.format_exc(), thread_id)

def get_thread_posts(board, thread_id):
	json_str = request_json('https://2ch.hk/' + board + '/res/' + thread_id + '.json')
	thread = json.loads(json_str)
	posts = list(map(
			lambda post: Post(str(post['num']), post['comment']),
			thread['threads'][0]['posts']))

	for post in posts:
		post.comment, post.reply_to = parse_post_html(post.comment)

	posts = list(filter(
			lambda post: post.comment,
			posts))

	return posts

def thread_posts_to_pairs(posts):
	posts = list(filter(
			lambda post: len(post.reply_to) <= 1,
			posts))

	map = {post.id: post for post in posts}
	pairs = []
	for post in posts:
		if len(post.reply_to) == 1 and post.reply_to[0] in map:
			pairs.append((map[post.reply_to[0]], post))

	return pairs

def request_json(url):
	req = urllib.request.Request(url)
	resp = urllib.request.urlopen(req)
	length = int(resp.getheader('Content-Length', 524288))
	json_str = resp.read(length).decode('utf-8')
	return json_str

def parse_post_html(post_html):
	parser = PostHTMLParser()
	parser.feed('<span>' + post_html + '</span>')
	post_text = parser.post

	post_lines = list(map(
			lambda line: line.strip(),
			post_text.split('\n')))
	post_lines = list(filter(
			lambda line: len(line) > 0,
			post_lines))
	return ('\n'.join(post_lines), parser.reply_to)


class Post:
	def __init__(self, id, comment, reply_to=[]):
		self.id = id
		self.comment = comment
		self.reply_to = reply_to

	def __repr__(self):
		return '<Post %s %s \'%s\'>' % (self.id, self.reply_to, self.comment)


class PostHTMLParser(HTMLParser):
	def __init__(self):
		super().__init__()
		self._in_reply_link = False
		self.post = ''
		self.reply_to = []

	def handle_starttag(self, tag, attrs):
		attrs = {attr[0]: attr[1] for attr in attrs}
		if tag == 'a' and 'class' in attrs and attrs['class'] == 'post-reply-link':
			self._in_reply_link = True
			self.reply_to.append(attrs['data-num'])
		if tag == 'br':
			self.post += '\n'

	def handle_data(self, data):
		if self._in_reply_link:
			return

		data = re.sub('\s+', ' ', data)

		if len(data.strip()) < 2:
			return

		self.post += data

	def handle_endtag(self, tag):
		if tag == 'a' and self._in_reply_link:
			self._in_reply_link = False


if __name__ == '__main__':
	parser = argparse.ArgumentParser()
	parser.add_argument(
			'--board',
			type=str,
			default='b')
	parser.add_argument(
			'--dataset_dir',
			type=str,
			default='./dataset/threads/')
	OPTS = parser.parse_args()

	try:
		main()
	except KeyboardInterrupt:
		sys.exit()
