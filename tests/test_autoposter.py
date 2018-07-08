import time
import pytest
import json
import re
import grub_threads
import autoposter
from autoposter import select_threads, thread_to_seed_tokens, Poster

class TestAutoposter:

	@pytest.fixture()
	def fake_request_for_select(self, monkeypatch):
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
		monkeypatch.setattr(grub_threads, 'request_json', request_json_fake)

	def test_select_threads(self, fake_request_for_select):
		threads = select_threads('b', 30, 1000, 50, 2000)
		assert(len(threads) == 3)
		assert(threads[0][0] == '0')
		assert(len(threads[0][1]) == 20)
		assert(threads[0][1][0].comment.startswith('Двач, помоги. Заебали соседи.'))
		assert(len(threads[1][1]) == 20)
		assert(threads[1][1][0].comment.startswith('Нет, не знаю, к сожалению.'))
		assert(len(threads[2][1]) == 19)

	def test_thread_to_seed_tokens(self, fake_request_for_select):
		threads = select_threads('b', 30, 1000, 50, 2000)
		seed = thread_to_seed_tokens(threads[0][1])
		assert(len(seed) > 100)
		assert(seed[0:10] == ['двач', ',', 'помоги', '.', 'заебали', 'соседи',
				'.', 'мало', 'того', ','])

	def test_thread_to_seed_tokens_with_tail(self, fake_request_for_select):
		threads = select_threads('b', 30, 1000, 50, 2000)
		seed = thread_to_seed_tokens(threads[0][1], (threads[1][1][0],))
		assert(len(seed) > 200)
		assert(seed[0:10] == ['двач', ',', 'помоги', '.', 'заебали', 'соседи',
				'.', 'мало', 'того', ','])
		assert(seed[-10:] == ['первый', 'день', ',', 'даже', 'не', 'первую',
				'неделю', '.', '<eol>', '<eoc>'])


	@pytest.fixture(autouse=True)
	def fake_opts(self, monkeypatch ):
		monkeypatch.setattr(autoposter, 'OPTS', OptsFake())

	@pytest.fixture()
	def poster(self, monkeypatch):
		monkeypatch.setattr(autoposter, 'generator', GeneratorFake())

		poster = Poster('some comment', None, '111', '222')

		self._posted_id = 123
		def post_fake(*args, **kwargs):
			print(args, kwargs)
			return {'Num': self._posted_id, 'Error': None, 'Status': 'OK'}
		monkeypatch.setattr(poster, '_post', post_fake)

		def sleep_fake():
			pass
		monkeypatch.setattr(poster, '_sleep', sleep_fake)

		return poster

	@pytest.fixture()
	def fake_request_for_replies(self, monkeypatch):
		def request_json_fake(url):
			with open('./tests/thread.json', 'rb') as f:
				return f.read().decode('utf-8')
		monkeypatch.setattr(grub_threads, 'request_json', request_json_fake)

	def test_poster(self, poster, fake_request_for_replies, capsys):
		poster.start()
		time.sleep(0.1)
		poster._stopped = True

		out = capsys.readouterr().out
		assert(out.endswith('/b/res/222.html#123\n'))

		err = capsys.readouterr().err
		assert(err == '')

	def test_poster_got_reply(self, poster, fake_request_for_replies, capsys):
		self._posted_id = 175409951

		poster.start()
		time.sleep(0.1)
		poster._stopped = True

		out = capsys.readouterr().out.split('\n')
		assert('============== NEW REPLY ==============' in out)
		assert('-> Какаю бабочками, писаю радугой. Ты просто за ручку не держался, поэтому не в курсе.' in out)

		err = capsys.readouterr().err
		assert(err == '')

	def test_poster_reply_to_reply(self, poster, fake_request_for_replies, capsys):
		self._posted_id = 175409951

		poster.start()
		time.sleep(0.1)
		poster._stopped = True

		assert(autoposter.posting_queue.get() == ('new generated reply', None, '222', '175410055'))

		err = capsys.readouterr().err
		assert(err == '')


class OptsFake():
	board = 'b'
	post_url = ''
	post_interval = 25
	passcode = ''
	watch_interval = 1

	max_threads = 30
	min_thread_len = 1000
	min_oppost_len = 50
	max_oppost_len = 2000

	max_res_len = 20

	pics_dir = ''


class GeneratorFake:
	def generate(self, seeds, min_res_len=3, max_res_len=20, callback=None):
		callback(0, ['new', 'generated', 'reply'])
