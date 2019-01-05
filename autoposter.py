import argparse
import os
import signal
import urllib.error
import api
from generate import Generator
from parse_dataset import comment_to_tokens
from filter_data import filter_data
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

	if OPTS.thread_id:
		selected_posts = select_thread_posts(
			OPTS.board,
			thread_id=OPTS.thread_id,
			max_posts=OPTS.max_posts,
			min_post_len=OPTS.min_post_len,
			max_post_len=OPTS.max_post_len
		)
		for post in selected_posts:
			produce_post(OPTS.thread_id, post)
	else:
		selected_threads = select_threads(
			OPTS.board,
			max_threads=OPTS.max_threads,
			min_post_len=OPTS.min_post_len,
			max_post_len=OPTS.max_post_len
		)
		for thread in selected_threads:
			thread_id, posts = thread
			produce_post(thread_id, posts[0])

	while True:
		time.sleep(1)


def produce_post(thread_id, reply_to):
	# TODO: filter_data
	seed_tokens = comment_to_tokens(reply_to.comment)
	gen_tokens = generator.generate(
		(seed_tokens,),
		forbidden_tokens=('<unk>',),
		min_res_len=3, max_res_len=OPTS.max_res_len
	)[0]

	comment = tokens_to_string(gen_tokens)
	pic_file = None
	if OPTS.pics_dir:
		pic_file = select_random_pic(OPTS.pics_dir)
	posting_queue.put((
		comment,
		pic_file,
		thread_id,
		reply_to
	))


class PostingRunner(threading.Thread):
	def __init__(self):
		super().__init__(name='poster', daemon=True)
		self._last_post_time = 0

	def run(self):
		while True:
			time_delta = time.time() - self._last_post_time
			if time_delta < OPTS.post_interval:
				time.sleep(OPTS.post_interval - time_delta)

			comment, pic_file, thread_id, reply_to = posting_queue.get()
			Poster(comment, pic_file, thread_id, reply_to).start()

			self._last_post_time = time.time()


class Poster(threading.Thread):
	def __init__(self, comment, pic_file, thread_id, reply_to):
		super().__init__(name=thread_id, daemon=True)
		self._comment = '>>%s\n%s' % (reply_to.id, comment)
		self._pic_file = pic_file
		self._thread_id = thread_id
		self._reply_to = reply_to
		self._stopped = False

	def run(self):
		response, id, link = api.post(
			self._comment,
			self._thread_id,
			OPTS.board,
			OPTS.passcode,
			self._pic_file
		)
		print('')
		if response['Error']:
			print(response)
			if response['Error'] == -8:
				print('Retry...')
				self._retry_pause()
				self.run()
		else:
			print(self._reply_to)
			print(self._comment)
			if self._pic_file:
				print('[' + os.path.basename(self._pic_file) + ']')
			print(link)
			self._watch_for_replies(id)

	def _watch_for_replies(self, post_id):
		seen = set()
		while not self._stopped:
			self._watcher_pause()

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

	def _get_replies(self, post_id):
		posts = api.get_thread_posts(OPTS.board, self._thread_id)
		replies = []
		for post in posts:
			if post_id in post.reply_to:
				replies.append(post)
		return replies

	def _reply(self, reply):
		produce_post(self._thread_id, reply)

	def _watcher_pause(self):
		time.sleep(OPTS.watch_interval)

	def _retry_pause(self):
		time.sleep(5)


def select_threads(
	board, max_threads,
	min_post_len, max_post_len
):
	selected_threads = []

	threads = api.get_threads(board)
	for thread_id in threads:
		posts = api.get_thread_posts(board, thread_id)
		if not posts:
			continue

		for post in posts:
			post.comment = filter_data(post.comment)

		seed_tokens = comment_to_tokens(posts[0].comment)
		if len(posts) >= 3 \
				and len(seed_tokens) >= min_post_len \
				and len(seed_tokens) <= max_post_len:
			selected_threads.append((thread_id, posts))

			if len(selected_threads) == max_threads:
				break

	return selected_threads

def select_thread_posts(
	board, thread_id, max_posts,
	min_post_len, max_post_len
):
	selected_posts = []

	posts = api.get_thread_posts(board, thread_id)
	random.shuffle(posts)

	for post in posts:
		post.comment = filter_data(post.comment)

		seed_tokens = comment_to_tokens(post.comment)
		if len(seed_tokens) >= min_post_len \
				and len(seed_tokens) <= max_post_len:
			selected_posts.append(post)

			if len(selected_posts) == max_posts:
				break

	return selected_posts

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
			if len(tokens) > i + 1 and tokens[i + 1] in ('к18', 'k18'):
				tokens[i] = ''
				tokens[i + 1] = '2k18'
			else:
				tokens[i] = str(random.randrange(0, 101, 1))

	res = ' '.join(tokens)
	res = re.sub(' ([.,:?)!;])', '\\1', res)
	res = re.sub('\s+', ' ', res)

	return res


def select_random_pic(dir):
	files = os.listdir(dir)
	file = random.choice(files)
	return os.path.join(dir, file)


if __name__ == '__main__':
	parser = argparse.ArgumentParser()
	parser.add_argument(
		'--weights_file',
		type=str,
		default='./models/weights.h5'
	)
	parser.add_argument(
		'--id2token_file',
		type=str,
		default='./models/id2token.json'
	)

	parser.add_argument(
		'--board',
		type=str,
		default='b'
	)
	parser.add_argument(
		'--passcode',
		type=str,
		required=True
	)
	parser.add_argument(
		'--post_interval',
		type=int,
		default=25,
		help='Interval between posting new comments (seconds)'
	)
	parser.add_argument(
		'--watch_interval',
		type=int,
		default=60,
		help='Interval for polling new replies (seconds)'
	)

	# Mode "reply to oppost in several threads"
	parser.add_argument(
		'--max_threads',
		type=int,
		default=30,
		help='Max amount of threads to reply'
	)

	# Mode "reply to several posts in one specified thread"
	parser.add_argument(
		'--thread_id',
		type=str,
		default='',
		help='Thread to reply'
	)
	parser.add_argument(
		'--max_posts',
		type=int,
		default=5,
		help='Max amount of posts in thread to reply'
	)

	parser.add_argument(
		'--min_post_len',
		type=int,
		default=10,
		help='Min post len to select (words)'
	)
	parser.add_argument(
		'--max_post_len',
		type=int,
		default=200,
		help='Max post len to select (words)'
	)

	parser.add_argument(
		'--max_res_len',
		type=int,
		default=30,
		help='Max len of generated response (words)'
	)

	parser.add_argument(
		'--pics_dir',
		type=str,
		default=''
	)

	OPTS = parser.parse_args()

	main()
