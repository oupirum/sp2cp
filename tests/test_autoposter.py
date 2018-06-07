import pytest
import json
import re
import download_threads
from autoposter import select_threads, thread_to_seed_tokens, check_replies

class TestAutoposter:
	def setup(self):
		print('')

	@pytest.fixture()
	def stub_request_for_select(self, monkeypatch):
		def request_json_fake(url):
			if url.endswith('threads.json'):
				return json.dumps({
					'threads': [
						{'comment': '', 'num': '0'},
						{'comment': '', 'num': '1'},
						{'comment': '', 'num': '2'},
						{'comment': '', 'num': '3'},
						{'comment': '', 'num': '4'},
					]
				})
			with open('./tests/thread.json', 'rb') as f:
				thread = json.loads(f.read().decode('utf-8'))
			i = int(re.fullmatch('.*?(\d)\.json', url).group(1))
			posts = thread['threads'][0]['posts']
			thread['threads'][0]['posts'] = posts[i*20:i*20+20]
			return json.dumps(thread, ensure_ascii=False)
		monkeypatch.setattr(download_threads, 'request_json', request_json_fake)

	def test_select_threads(self, stub_request_for_select):
		threads = select_threads('b', 30, 1000, 50, 2000)
		assert(len(threads) == 3)
		assert(len(threads[0][1]) == 20)
		assert(threads[0][1][0].comment.startswith('Двач, помоги. Заебали соседи.'))
		assert(len(threads[1][1]) == 20)
		assert(threads[1][1][0].comment.startswith('Нет, не знаю, к сожалению.'))
		assert(len(threads[2][1]) == 19)

	def test_thread_to_seed_tokens(self, stub_request_for_select):
		threads = select_threads('b', 30, 1000, 50, 2000)
		seed = thread_to_seed_tokens(threads[0][1], 1000, 3)
		assert(len(seed) > 10)
		assert(seed[0:10] == ['двач', ',', 'помоги', '.', 'заебали', 'соседи',
				'.', 'мало', 'того', ','])


	@pytest.fixture()
	def stub_request_for_replies(self, monkeypatch):
		def request_json_fake(url):
			with open('./tests/thread.json', 'rb') as f:
				return f.read().decode('utf-8')
		monkeypatch.setattr(download_threads, 'request_json', request_json_fake)

	def test_check_replies(self, stub_request_for_replies):
		replies = check_replies('175407040', '123', 'b')
		print(replies)
		assert(len(replies) == 3)
		assert(replies[0].id == '175407182')
