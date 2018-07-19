import argparse
import os
import signal
import urllib.error
from grub_threads import get_threads, get_thread_posts, Post
from generate import Generator
from parse_dataset import comment_to_tokens
import requests
import time
import random
import re
import threading
import queue
from transliterate import translit

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
			OPTS.min_seed_len,
			OPTS.max_seed_len)
	for thread in selected_threads:
		produce_post(thread)

	while True:
		time.sleep(1)

# TODO: refactor

def produce_post(thread, reply_to=None):
	thread_id, posts = thread

	tail = []
	if reply_to:
		tail.append(reply_to)

	seed_tokens = thread_to_seed_tokens(posts, tail)
	print('seed len:', len(seed_tokens))

	def generated(i, gen_tokens, seed_tokens):
		seed = tokens_to_string(seed_tokens)
		comment = tokens_to_string(gen_tokens)
		pic_file = None
		if OPTS.pics_dir:
			pic_file = select_random_pic(OPTS.pics_dir)
		posting_queue.put((
			comment,
			pic_file,
			thread_id,
			Post(reply_to.id if reply_to else thread_id, seed)
		))

	generator.generate(
			(seed_tokens,),
			forbidden_tokens=('<unk>',),
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

			comment, pic_file, thread_id, reply_to = posting_queue.get()
			Poster(comment, pic_file, reply_to, thread_id).start()

			self._last_post_time = time.time()


class Poster(threading.Thread):
	def __init__(self, comment, pic_file, reply_to, thread_id):
		super().__init__(name=thread_id, daemon=True)
		self._thread_url = 'https://2ch.hk/%s/res/%s.html' \
				% (OPTS.board, thread_id)
		self._comment = ('>>%s' % reply_to.id) \
				+ '\n' \
				+ comment
		self._pic_file = pic_file
		self._reply_to = reply_to
		self._thread_id = thread_id
		self._stopped = False

	def run(self):
		response = self._post()
		print('')
		if response['Error']:
			print(response)
		else:
			print(self._reply_to)
			print(self._comment)
			if self._pic_file:
				print(os.path.basename(self._pic_file))
			post_id = str(response['Num'])
			print(self._thread_url + '#' + post_id)
			self._watch_for_replies(post_id)

	def _post(self):
		formdata = {
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
		}

		if self._pic_file:
			pic_name = translit(os.path.basename(
					self._pic_file), 'ru', reversed=True)
			formdata['formimages[]'] = (pic_name, open(self._pic_file, 'rb'))

		response = requests.post(
				OPTS.post_url,
				files=formdata,
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
		posts = get_thread_posts(OPTS.board, self._thread_id)
		replies = []
		for post in posts:
			if post_id in post.reply_to:
				replies.append(post)
		return replies

	def _reply(self, reply):
		posts = get_thread_posts(OPTS.board, self._thread_id)
		thread = (self._thread_id, posts)
		produce_post(thread, reply)


def select_threads(board, max_threads,
		min_seed_len, max_seed_len):
	selected_threads = []

	threads = get_threads(board)
	for thread_id in threads:
		posts = get_thread_posts(board, thread_id)
		if not posts:
			continue

		seed_tokens = thread_to_seed_tokens(posts)
		if len(posts) >= 3 \
				and len(seed_tokens) >= min_seed_len \
				and len(seed_tokens) <= max_seed_len:
			selected_threads.append((thread_id, posts))

			if len(selected_threads) == max_threads:
				break

	return selected_threads

def thread_to_seed_tokens(thread_posts, tail_posts=()):
	tokens = comment_to_tokens(thread_posts[0].comment)
	for post in tail_posts:
		tokens.extend(comment_to_tokens(post.comment))
	return tokens

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
			'--min_seed_len',
			type=int,
			default=10,
			help='Min OP post len (words)')
	parser.add_argument(
			'--max_seed_len',
			type=int,
			default=200,
			help='Max OP post len (words)')

	parser.add_argument(
			'--max_res_len',
			type=int,
			default=30,
			help='Max len of generated response (words)')

	parser.add_argument(
			'--pics_dir',
			type=str,
			default='')

	OPTS = parser.parse_args()

	main()
