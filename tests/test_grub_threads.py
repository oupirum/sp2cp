import grub_threads
from grub_threads import \
		parse_post_html, \
		get_threads, \
		get_thread_posts, \
		thread_posts_to_pairs
import json

class TestGrubThreads:

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

		posts = get_thread_posts('b', '123')

		assert(len(posts) == 100)
		assert(posts[6].id == '175407315')
		assert(posts[6].comment == ''
				'Да, замочная скважина у них такая, что ничего не засунуть - '
				'пробовала вчера. Она какая-то скрытая, блин.\nДа и за '
				'хулиганство уехать не охота.')
		assert(posts[6].reply_to == [])

	def test_thread_posts_to_pairs(self, monkeypatch):
		def request_fake(url):
			with open('./tests/thread.json', 'rb') as f:
				return f.read().decode('utf-8')
		monkeypatch.setattr(grub_threads, 'request_json', request_fake)

		posts = get_thread_posts('b', '123')
		pairs = thread_posts_to_pairs(posts)

		assert(len(pairs) == 64)

		pair = list(filter(lambda p: p[0].id == '175406614' and p[1].id == '175406863', pairs))[0]
		assert(pair[0].comment.startswith('Двач, помоги. Заебали соседи.'))
		assert(pair[1].comment.startswith('Переезжай ко мне'))

		pair = list(filter(lambda p: p[0].id == '175410617' and p[1].id == '175410701', pairs))[0]
		assert(pair[0].comment.startswith('А по батареям постучать?'))
		assert(pair[1].comment.startswith('По батареям стучать - всем мешать.\nА еще тут вчера'))


	def test_get_threads_real_request(self):
		threads = get_threads('b')

		assert(len(threads) > 0)
		assert(isinstance(threads[1], str))
		assert(len(threads[1]) > 0)

	def test_get_thread_posts_real_request(self):
		threads = get_threads('b')
		posts = get_thread_posts('b', threads[0])

		assert(len(posts) > 0)
		assert(isinstance(posts[0].id, str))
		assert(isinstance(posts[0].comment, str))
		assert(isinstance(posts[0].reply_to, list))


	def test_parse_post_html(self):
		with open('./tests/thread.json', 'rb') as f:
			posts = json.loads(f.read().decode('utf-8'))['threads'][0]['posts']

			comment, reply_to = parse_post_html(posts[18]['comment'])
			assert(comment == ''
					'> /b\n'
					'> Помогать дыре в мясе\n'
					'А ты смешной.')
			assert(reply_to == [])

	def test_parse_post_html_with_replies(self):
		with open('./tests/thread.json', 'rb') as f:
			posts = json.loads(f.read().decode('utf-8'))['threads'][0]['posts']

			comment, reply_to = parse_post_html(posts[16]['comment'])
			assert(comment == 'Привет. Я хочу твой задний проход.')
			assert(reply_to == ['175406614'])

			comment, reply_to = parse_post_html(posts[71]['comment'])
			assert(comment.startswith('Дебил потралил двач.'))
			assert(reply_to == ['175409678', '175409756', '175409770'])
