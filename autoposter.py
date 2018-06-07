import argparse
import urllib.error
from download_threads import get_threads, get_thread_posts
from generate import generate
from parse_dataset import thread_to_tokens
import requests
import time
import random
import re
import threading

# weights_file = './models/200000_100_plain/weights_b9500.h5'
# id2token_file = './models/200000_100_plain/id2token.json'

post_interval = 25
last_post_time = 0

def main():
	selected_threads = select_threads(
			OPTS.board,
			OPTS.max_select_threads,
			OPTS.min_thread_len,
			OPTS.min_oppost_len,
			OPTS.max_oppost_len)
	seeds = []
	for i, thread in enumerate(selected_threads):
		seed_tokens = thread_to_seed_tokens(thread[1], OPTS.max_post_len, OPTS.last_posts_num)
		print(len(seed_tokens))
		seeds.append(seed_tokens)

	def generated(i, gen_tokens):
		global last_post_time
		time_delta = time.time() - last_post_time
		if time_delta < post_interval:
			time.sleep(post_interval - time_delta)
		last_post_time = time.time()

		thread_id = str(selected_threads[i][0])
		thread = threading.Thread(
				name=thread_id,
				daemon=True,
				target=post,
				args=(gen_tokens, thread_id))
		thread.start()

	generate(OPTS.weights_file, OPTS.id2token_file,
			seeds,
			min_res_len=3, max_res_len=30,
			callback=generated)

	while True:
		time.sleep(1)


def post(gen_tokens, thread_id):
	thread_url = 'https://2ch.hk/%s/res/%s.html' % (OPTS.board, thread_id)
	comment = '>>%s' % (thread_id,) \
			+ '\n' \
			+ tokens_to_string(gen_tokens)
	print('')
	print(comment)
	response = requests.post(
			OPTS.post_url,
			files={
				'task': (None, 'post'),
				'board': (None, OPTS.board),
				'thread': (None, thread_id),
				'comment': (None, comment),
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
				'Referer': thread_url,
				'Host': '2ch.hk',
				'Origin': 'https://2ch.hk',
				'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/66.0.3359.170 Safari/537.36',
			})
	print(response.json())
	if not response.json()['Error']:
		post_id = str(response.json()['Num'])
		print(thread_url + '#' + str(post_id))
		watch_for_replies(post_id, thread_id, OPTS.board, comment, 120)

def watch_for_replies(post_id, thread_id, board, comment, interval):
	seen = set()
	while True:
		time.sleep(interval)
		replies = []
		try:
			replies = check_replies(post_id, thread_id, board)
		except urllib.error.HTTPError as err:
			print('HTTPError:', err.code, err.reason)
			print('watchers left:', threading.active_count() - 2)
			break
		except Exception as err:
			print(err)
		for reply in replies:
			if reply.id not in seen:
				seen.add(reply.id)
				print('')
				print('NEW REPLY')
				print(comment)
				print('>>>>>>', reply.comment)
				print('https://2ch.hk/%s/res/%s.html#%s'
						% (board, thread_id, post_id))

def check_replies(post_id, thread_id, board):
	posts = get_thread_posts(board, thread_id, set())
	replies = []
	for post in posts:
		if post_id in post.reply_to:
			replies.append(post)
	return replies


def select_threads(board, max_selected_threads, min_thread_len,
		min_oppost_len, max_oppost_len):
	# TODO: refactor: parse_utils
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
			if len(selected_threads) == max_selected_threads:
				break
	return selected_threads

def thread_to_seed_tokens(thread_posts, max_post_len, last_posts_num):
	comments = [post.comment for post in thread_posts]
	seed = ''
	seed += comments[0] + '\n\n'
	if last_posts_num > 0:
		comments = list(filter(
				lambda c: len(c) <= max_post_len,
				comments[1:]))
		last_comments = comments[-last_posts_num:]
		for comment in last_comments:
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
			tokens[i] = str(random.randrange(1, 101, 1))

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
			'--passcode',
			type=str,
			default='dde373b2902b3fe0442444ddfc737aeccc9d6ee0bc581ea4d965628495848cb3')

	parser.add_argument(
			'--max_select_threads',
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
			'--max_post_len',
			type=int,
			default=1000,
			help='Max post len (chars)')

	parser.add_argument(
			'--last_posts_num',
			type=int,
			default=3,
			help='How many comments to use to create seed sequence')
	OPTS = parser.parse_args()

	main()
