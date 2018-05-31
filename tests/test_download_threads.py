from download_threads import \
		parse_post_html, \
		get_threads, \
		get_thread_posts
import json

class TestDownloadThreads:
	def setup(self):
		print('')

	def test_parse_post_html(self):
		with open('./tests/fake_thread.json', 'rb') as f:
			posts = json.loads(f.read().decode('utf-8'))['threads'][0]['posts']

			post_text = parse_post_html(posts[16]['comment'])
			assert(post_text == 'Привет. Я хочу твой задний проход.')

			post_text = parse_post_html(posts[18]['comment'])
			assert(post_text == '/b\n'
					'Помогать дыре в мясе\n'
					'А ты смешной.')

	def test_get_threads(self):
		threads = get_threads('b')

		assert(len(threads) > 0)
		assert(isinstance(threads[1], str))
		assert(len(threads[1]) > 0)

	def test_get_thread_posts(self):
		threads = get_threads('b')
		posts = get_thread_posts('b', threads[0])

		assert(len(posts) > 0)
		assert(isinstance(posts[0][0], str))
		assert(isinstance(posts[0][1], str))
