import argparse
import re
import urllib.request
from html.parser import HTMLParser
import os
import json
import time
import traceback
import sys

readen_post_ids = set()

def main():
	os.makedirs(OPTIONS.dataset_dir, exist_ok=True)

	readen_post_ids_path = os.path.join(OPTIONS.dataset_dir, 'saved_post_ids.txt')
	if os.path.exists(readen_post_ids_path):
		with open(readen_post_ids_path, 'r') as f:
			readen_post_ids.update(f.read().split('\n'))
			print('readen_post_ids', len(readen_post_ids))

	while True:
		try:
			threads = get_threads(OPTIONS.board)
			for thread_id in threads:
				process_thread(thread_id, OPTIONS.board, OPTIONS.dataset_dir)
		finally:
			with open(readen_post_ids_path, 'w') as f:
				f.write('\n'.join(readen_post_ids))

		print('pause...')
		time.sleep(1800)

def process_thread(thread_id, board, ds_dir):
	try:
		posts = get_thread_posts(board, thread_id, readen_post_ids)
		print(len(readen_post_ids))
		if len(posts) == 0:
			return

		with open(
				os.path.join(ds_dir, thread_id + '.txt'),
				'ab') as f:
			comments = [post[1] for post in posts]
			comments = '\n\n'.join(comments) + '\n\n'
			f.write(comments.encode('utf-8'))
			print(comments)
	except KeyboardInterrupt:
		raise
	except:
		print(traceback.format_exc(), thread_id)

def get_threads(board):
	json_str = request_json('https://2ch.hk/' + board + '/threads.json')
	threads = json.loads(json_str)
	thread_ids = list(map(
			lambda thread: thread['num'],
			threads['threads']))
	return thread_ids

def get_thread_posts(board, thread_id, readen_post_ids):
	json_str = request_json('https://2ch.hk/' + board + '/res/' + thread_id + '.json')
	thread = json.loads(json_str)
	posts = list(map(
			lambda post: (str(post['num']), post['comment']),
			thread['threads'][0]['posts']))

	posts = list(filter(
			lambda post: post[0] not in readen_post_ids,
			posts))
	if len(posts) > 0:
		ids = [post[0] for post in posts]
		readen_post_ids.update(ids)

	posts = list(map(
			lambda post: (post[0], parse_post_html(post[1])),
			posts))
	posts = list(filter(
			lambda post: post[1],
			posts))

	return posts

def request_json(url):
	req = urllib.request.Request(url)
	resp = urllib.request.urlopen(req)
	if resp.status != 200:
		raise Exception('Error on request %s (%d: %s)'
				% (url, resp.status, resp.reason))
	json_str = resp.read().decode('utf-8')
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
	return '\n'.join(post_lines)


class PostHTMLParser(HTMLParser):
	_in_reply_link = False
	post = ''

	def handle_starttag(self, tag, attrs):
		id = None
		cls = None
		for attr in attrs:
			if attr[0] == 'id':
				id = attr[1]
			if attr[0] == 'class':
				cls = attr[1]
		if tag == 'a' and cls == 'post-reply-link':
			self._in_reply_link = True
		if tag == 'br':
			self.post += '\n'

	def handle_data(self, data):
		if self._in_reply_link:
			return

		data = re.sub('\s+', ' ', data)

		if data.startswith('>'):
			data = data[1:]

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
	OPTIONS = parser.parse_args()

	try:
		main()
	except KeyboardInterrupt:
		sys.exit()
