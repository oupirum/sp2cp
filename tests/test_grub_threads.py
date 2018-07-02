import grub_threads
from grub_threads import \
		parse_post_html, \
		get_threads, \
		get_thread_posts
import json

class TestGrubThreads:
	def test_parse_post_html(self):
		with open('./tests/thread.json', 'rb') as f:
			posts = json.loads(f.read().decode('utf-8'))['threads'][0]['posts']

			comment, reply_to = parse_post_html(posts[16]['comment'])
			assert(comment == 'Привет. Я хочу твой задний проход.')
			assert(reply_to == ['175406614'])

			comment, reply_to = parse_post_html(posts[18]['comment'])
			assert(comment == ''
					'/b\n'
					'Помогать дыре в мясе\n'
					'А ты смешной.')
			assert(reply_to == [])


	def test_get_threads(self, monkeypatch):
		def request_fake(url):
			with open('./tests/threads.json', 'rb') as f:
				return f.read().decode('utf-8')
		monkeypatch.setattr(grub_threads, 'request_json', request_fake)

		threads = get_threads('b')

		assert(len(threads) == 206)
		assert(threads[0:3] == ['176973002', '176973994', '176968447'])

	def test_get_thread_posts(self, monkeypatch):
		def request_fake(url):
			with open('./tests/thread.json', 'rb') as f:
				return f.read().decode('utf-8')
		monkeypatch.setattr(grub_threads, 'request_json', request_fake)

		posts = get_thread_posts('b', '123', set())

		assert(len(posts) == 100)
		assert(posts[6].id == '175407315')
		assert(posts[6].comment == ''
				'Да, замочная скважина у них такая, что ничего не засунуть - '
				'пробовала вчера. Она какая-то скрытая, блин.\nДа и за '
				'хулиганство уехать не охота.')
		assert(posts[6].reply_to == [])


	def test_get_threads_real_request(self):
		threads = get_threads('b')

		assert(len(threads) > 0)
		assert(isinstance(threads[1], str))
		assert(len(threads[1]) > 0)

	def test_get_thread_posts_real_request(self):
		threads = get_threads('b')
		posts = get_thread_posts('b', threads[0], set())

		assert(len(posts) > 0)
		assert(isinstance(posts[0].id, str))
		assert(isinstance(posts[0].comment, str))
		assert(isinstance(posts[0].reply_to, list))
