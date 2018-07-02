import argparse
import os
import signal
import urllib.error
from grub_threads import get_threads, get_thread_posts
from generate import Generator
from parse_dataset import thread_to_tokens
import requests
import time
import random
import re
import threading
import queue

OPTS = None
posting_queue = queue.Queue()
generator = None

def main():
	global generator
	generator = Generator(OPTS.weights_file, OPTS.id2token_file)

	PostingRunner().start()

	selected_threads = select_threads(
			OPTS.board,
			OPTS.max_threads,
			OPTS.min_thread_len,
			OPTS.min_oppost_len,
			OPTS.max_oppost_len)
	for thread in selected_threads:
		produce_comment(thread)

	while True:
		time.sleep(1)


def produce_comment(thread, reply_to=None):
	thread_id, posts = thread

	tail = []
	if reply_to:
		tail.append(reply_to.comment)

	seed_tokens = thread_to_seed_tokens(posts, OPTS.max_post_len, OPTS.use_posts, tail)
	print(len(seed_tokens))

	def generated(i, gen_tokens):
		comment = tokens_to_string(gen_tokens)
		posting_queue.put((
			comment,
			thread_id,
			reply_to.id if reply_to else thread_id
		))

	generator.generate(
			(seed_tokens,),
			min_res_len=3, max_res_len=OPTS.max_res_len,
			callback=generated)


class PostingRunner(threading.Thread):
	def __init__(self):
		super().__init__(name='poster', daemon=True)
		self._last_post_time = 0

	def run(self):
		while True:
			time_delta = time.time() - self._last_post_time
			if time_delta < OPTS.post_interval:
				time.sleep(OPTS.post_interval - time_delta)

			comment, thread_id, reply_to = posting_queue.get()
			Poster(comment, reply_to, thread_id).start()

			self._last_post_time = time.time()


class Poster(threading.Thread):
	def __init__(self, comment, reply_to, thread_id):
		super().__init__(name=thread_id, daemon=True)
		self._thread_url = 'https://2ch.hk/%s/res/%s.html' % (OPTS.board, thread_id)
		self._comment = ('>>%s' % reply_to) \
				+ '\n' \
				+ comment
		self._thread_id = thread_id
		self._stopped = False

	def run(self):
		response = self._post()
		print('')
		if response['Error']:
			print(response)
		else:
			print(self._comment)
			post_id = str(response['Num'])
			print(self._thread_url + '#' + post_id)
			self._watch_for_replies(post_id)

	def _post(self):
		# TODO: attach random pic
		response = requests.post(
				OPTS.post_url,
				files={
					'task': (None, 'post'),
					'board': (None, OPTS.board),
					'thread': (None, self._thread_id),
					'comment': (None, self._comment),
					'email': (None, ''),
					'usercode': (None, OPTS.passcode),
					'code': (None, ''),
					'captcha_type': (None, 'invisible_recaptcha'),
					'oekaki_image': (None, ''),
					'oekaki_metadata': (None, ''),
				},
				cookies={
					'passcode_auth': OPTS.passcode,
				},
				headers={
					'Accept': 'application/json',
					'Cache-Control': 'no-cache',
					'Referer': self._thread_url,
					'Host': '2ch.hk',
					'Origin': 'https://2ch.hk',
					'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/66.0.3359.170 Safari/537.36',
				})
		return response.json()

	def _watch_for_replies(self, post_id):
		seen = set()
		while not self._stopped:
			self._sleep()

			replies = []
			try:
				replies = self._get_replies(post_id)
			except urllib.error.HTTPError as err:
				print('')
				print('HTTPError:', err.code, err.reason)

				n_left = threading.active_count() - 3
				print('watchers left:', n_left)
				if n_left == 0:
					os.kill(os.getpid(), signal.SIGINT)

				break
			except Exception as err:
				print('')
				print(err)

			for reply in replies:
				if reply.id not in seen:
					seen.add(reply.id)

					print('')
					print('============== NEW REPLY ==============')
					print(self._comment)
					print('->', reply.comment)
					print('https://2ch.hk/%s/res/%s.html#%s'
							% (OPTS.board, self._thread_id, post_id))

					self._reply(reply)

	def _sleep(self):
		time.sleep(OPTS.watch_interval)

	def _get_replies(self, post_id):
		posts = get_thread_posts(OPTS.board, self._thread_id, set())
		replies = []
		for post in posts:
			if post_id in post.reply_to:
				replies.append(post)
		return replies

	def _reply(self, reply):
		posts = get_thread_posts(OPTS.board, self._thread_id, set())
		thread = (self._thread_id, posts)
		produce_comment(thread, reply)


def select_threads(board, max_threads, min_thread_len,
		min_oppost_len, max_oppost_len):
	threads = get_threads(board)

	selected_threads = []
	for thread_id in threads:
		posts = get_thread_posts(board, thread_id, set())
		if not posts:
			continue

		thread_len = len(''.join([post.comment for post in posts]))
		oppost_len = len(posts[0].comment)
		num_posts = len(posts)
		if thread_len >= min_thread_len \
				and oppost_len >= min_oppost_len \
				and oppost_len <= max_oppost_len \
				and num_posts >= 3:
			selected_threads.append((thread_id, posts))

			if len(selected_threads) == max_threads:
				break

	return selected_threads

def thread_to_seed_tokens(thread_posts, max_post_len, use_posts, tail=()):
	comments = [post.comment for post in thread_posts]

	seed = ''
	seed += comments[0] + '\n\n'

	if use_posts > 0:
		comments = list(filter(
				lambda c: len(c) <= max_post_len,
				comments[1:]))
		last_comments = comments[-use_posts:]
		for comment in last_comments:
			seed += comment + '\n\n'

	for comment in tail:
		seed += comment + '\n\n'

	seed_tokens = thread_to_tokens(seed)
	return seed_tokens

def tokens_to_string(tokens):
	start = 0
	for i, token in enumerate(tokens):
		if not re.fullmatch('(<eol>)|(<eoc>)|(<pad>)|[.,:?)!;]+', token):
			start = i
			break
	tokens = tokens[start:]

	for i, token in enumerate(tokens):
		if token == '<eol>':
			tokens[i] = '\n'
		if token in ['<eoc>', '<pad>', '<unk>']:
			tokens[i] = ''
		if token == '<n>':
			tokens[i] = str(random.randrange(0, 101, 1))

	res = ' '.join(tokens)
	res = re.sub(' ([.,:?)!;])', '\\1', res)
	res = re.sub('\s+', ' ', res)

	return res


if __name__ == '__main__':
	parser = argparse.ArgumentParser()
	parser.add_argument(
			'--weights_file',
			type=str,
			default='./models/weights.h5')
	parser.add_argument(
			'--id2token_file',
			type=str,
			default='./models/id2token.json')

	parser.add_argument(
			'--board',
			type=str,
			default='b')
	parser.add_argument(
			'--post_url',
			type=str,
			default='https://2ch.hk/makaba/posting.fcgi?json=1')
	parser.add_argument(
			'--post_interval',
			type=int,
			default=25,
			help='Interval between posting new comments (seconds)')
	parser.add_argument(
			'--passcode',
			type=str,
			required=True)
	parser.add_argument(
			'--watch_interval',
			type=int,
			default=120,
			help='Interval for polling new replies (seconds)')

	parser.add_argument(
			'--max_threads',
			type=int,
			default=30,
			help='Max amount of threads to post')
	parser.add_argument(
			'--min_thread_len',
			type=int,
			default=1000,
			help='Min thread len to select (chars)')
	parser.add_argument(
			'--min_oppost_len',
			type=int,
			default=50,
			help='Min OP post len (chars)')
	parser.add_argument(
			'--max_oppost_len',
			type=int,
			default=2000,
			help='Max OP post len (chars)')

	parser.add_argument(
			'--use_posts',
			type=int,
			default=0,
			help='How many comments to use to create seed sequence')
	parser.add_argument(
			'--max_post_len',
			type=int,
			default=1000,
			help='Max post len (chars)')

	parser.add_argument(
			'--max_res_len',
			type=int,
			default=30,
			help='Max len of generated response (words)')

	OPTS = parser.parse_args()

	main()
