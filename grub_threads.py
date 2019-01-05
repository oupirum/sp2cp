import argparse
import os
import time
import traceback
import sys
from filter_data import filter_data
import api

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
			threads = api.get_threads(OPTS.board, OPTS.passcode)
			for thread_id in threads:
				comments = read_thread(thread_id, OPTS.board, OPTS.passcode)
				if comments:
					print(comments)
					with open(
						os.path.join(OPTS.dataset_dir, thread_id + '.txt'),
						'ab'
					) as f:
						f.write(comments.encode('utf-8'))
		finally:
			with open(readen_post_ids_file, 'w') as f:
				f.write('\n'.join(readen_post_ids))

		print('pause...')
		time.sleep(900)

def read_thread(thread_id, board, passcode=''):
	try:
		posts = api.get_thread_posts(board, thread_id, passcode)

		for post in posts:
			post.comment = filter_data(post.comment)
		posts = list(filter(
			lambda post: len(post.comment) > 1,
			posts
		))

		pairs = thread_posts_to_pairs(posts)

		pairs = list(filter(
			lambda pair: pair[1].id not in readen_post_ids,
			pairs
		))
		if len(pairs) == 0:
			return

		ids = [post.id for post in posts]
		readen_post_ids.update(ids)
		print('posts readen:', len(readen_post_ids))

		comments = [pair[0].comment + '\n\n' + pair[1].comment for pair in pairs]
		return '\n\n'.join(comments) + '\n\n'
	except KeyboardInterrupt:
		raise
	except:
		print(traceback.format_exc(), thread_id)

def thread_posts_to_pairs(posts):
	posts = list(filter(
		lambda post: len(post.reply_to) <= 1,
		posts
	))

	map = {post.id: post for post in posts}
	pairs = []
	for post in posts:
		if len(post.reply_to) == 1 and post.reply_to[0] in map:
			pairs.append((map[post.reply_to[0]], post))

	return pairs


if __name__ == '__main__':
	parser = argparse.ArgumentParser()
	parser.add_argument(
		'--board',
		type=str,
		default='b'
	)
	parser.add_argument(
		'--dataset_dir',
		type=str,
		default='./dataset/threads/'
	)

	parser.add_argument(
		'--passcode',
		type=str,
		default=''
	)

	OPTS = parser.parse_args()

	try:
		main()
	except KeyboardInterrupt:
		sys.exit()
