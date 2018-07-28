from grub_threads import parse_thread, thread_posts_to_pairs
import api

class TestGrubThreads:

	def test_parse_thread(self, monkeypatch):
		def request_fake(url):
			with open('./tests/thread.json', 'rb') as f:
				return f.read().decode('utf-8')
		monkeypatch.setattr(api, 'request_json', request_fake)

		comments = parse_thread('123', 'b')

		assert('Переезжай ко мне\n\n'
				'Я умру от недосыпа быстрее, чем соберу вещи.\n\n' in comments)
		assert('Отнесу на руках тебя. Город?\n\n'
				'А ты хорош)\nмимопроходил\n\n' in comments)
		assert(comments.endswith('Пьяные голоса пообещали размотать.\n\n'))
		assert(len(comments) == 20500)

	def test_thread_posts_to_pairs(self, monkeypatch):
		def request_fake(url):
			with open('./tests/thread.json', 'rb') as f:
				return f.read().decode('utf-8')
		monkeypatch.setattr(api, 'request_json', request_fake)

		posts = api.get_thread_posts('b', '123')
		pairs = thread_posts_to_pairs(posts)

		pair = list(filter(lambda p: p[0].id == '175406614' and p[1].id == '175406863', pairs))[0]
		assert(pair[0].comment.startswith('Двач, помоги. Заебали соседи.'))
		assert(pair[1].comment.startswith('Переезжай ко мне'))

		pair = list(filter(lambda p: p[0].id == '175410617' and p[1].id == '175410701', pairs))[0]
		assert(pair[0].comment.startswith('А по батареям постучать?'))
		assert(pair[1].comment.startswith('По батареям стучать - всем мешать.\nА еще тут вчера'))

		assert(len(pairs) == 64)
