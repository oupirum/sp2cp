import time
import pytest
import json
import re
import autoposter
from autoposter import select_threads, Poster
import api

class TestAutoposter:

	@pytest.fixture(autouse=True)
	def fake_opts(self, monkeypatch):
		monkeypatch.setattr(autoposter, 'OPTS', OptsFake())

	@pytest.fixture()
	def fake_request_for_select(self, monkeypatch):
		def request_json_fake(url, passcode=''):
			if url.endswith('threads.json'):
				return {
					'threads': [
						{'comment': '', 'num': '0'},
						{'comment': '', 'num': '1'},
						{'comment': '', 'num': '2'},
						{'comment': '', 'num': '3'},
						{'comment': '', 'num': '4'},
					]
				}
			with open('./tests/thread.json', 'rb') as f:
				thread = json.loads(f.read().decode('utf-8'))
			i = int(re.fullmatch('.*?(\d)\.json', url).group(1))
			posts = thread['threads'][0]['posts']
			thread['threads'][0]['posts'] = posts[i*20:i*20+20]
			return thread
		monkeypatch.setattr(api, 'request_json', request_json_fake)

	def test_select_threads(self, fake_request_for_select):
		threads = select_threads('b', 30, 10, 200)
		assert(len(threads) == 3)
		assert(threads[0][0] == '0')
		assert(len(threads[0][1]) == 20)
		assert(threads[0][1][0].comment.startswith('Двач, помоги. Заебали соседи.'))
		assert(len(threads[1][1]) == 20)
		assert(threads[1][1][0].comment.startswith('Нет, не знаю, к сожалению.'))
		assert(len(threads[2][1]) == 19)


	@pytest.fixture()
	def fake_request_for_replies(self, monkeypatch):
		def request_json_fake(url, passcode=''):
			with open('./tests/thread.json', 'rb') as f:
				return json.loads(f.read().decode('utf-8'))
		monkeypatch.setattr(api, 'request_json', request_json_fake)

	def fake_poster(self, monkeypatch, post_id, error=None):
		monkeypatch.setattr(autoposter, 'generator', GeneratorFake())

		def post_fake(*args, **kwargs):
			return ({'Num': post_id, 'Error': poster._error, 'Status': 'OK'}, post_id, 'http://post_url')
		monkeypatch.setattr(api, 'post', post_fake)

		poster = Poster('some comment', None, 'thread_id', api.Post('reply_to_id', 'reply_to_comment'))
		poster._error = error

		def sleep_fake():
			time.sleep(0.01)
		monkeypatch.setattr(poster, '_watcher_pause', sleep_fake)
		monkeypatch.setattr(poster, '_retry_pause', sleep_fake)

		return poster

	def test_poster(self, monkeypatch, fake_request_for_replies, capsys):
		poster = self.fake_poster(monkeypatch, '123')
		poster.start()
		time.sleep(0.02)
		poster._stopped = True

		out = capsys.readouterr().out
		assert(out == '\n<Post reply_to_id () \'reply_to_comment\'>\n>>reply_to_id\nsome comment\nhttp://post_url\n')

		err = capsys.readouterr().err
		assert(err == '')

	def test_poster_retry(self, monkeypatch, fake_request_for_replies, capsys):
		poster = self.fake_poster(monkeypatch, '123', -8)
		poster.start()
		time.sleep(0.02)
		poster._error = None
		time.sleep(0.02)
		poster._stopped = True

		out = capsys.readouterr().out
		assert('\nRetry...\n' in out)
		assert(out.endswith('<Post reply_to_id () \'reply_to_comment\'>\n>>reply_to_id\nsome comment\nhttp://post_url\n'))

		err = capsys.readouterr().err
		assert(err == '')

	def test_poster_got_reply(self, monkeypatch, fake_request_for_replies, capsys):
		poster = self.fake_poster(monkeypatch, '175409951')
		poster.start()
		time.sleep(0.04)
		poster._stopped = True

		out = capsys.readouterr().out.split('\n')
		assert('============== NEW REPLY ==============' in out)
		assert('-> Какаю бабочками, писаю радугой. Ты просто за ручку не держался, поэтому не в курсе.' in out)

		err = capsys.readouterr().err
		assert(err == '')

		assert(autoposter.posting_queue.empty() == False)
		comment, pic_file, thread_id, reply_to = autoposter.posting_queue.get()
		assert(comment == 'new generated reply')
		assert(pic_file == None)
		assert(thread_id == 'thread_id')
		assert(reply_to.id == '175410055')
		assert(reply_to.comment == 'Какаю бабочками, писаю радугой. Ты просто за ручку не держался, поэтому не в курсе.')


class OptsFake():
	board = 'b'
	post_interval = 25
	passcode = ''
	watch_interval = 1

	max_threads = 30
	thread_id = ''
	max_posts = 5
	min_post_len = 50
	max_post_len = 2000

	max_res_len = 20

	pics_dir = ''


class GeneratorFake:
	def generate(self, seeds, forbidden_tokens=(), min_res_len=3, max_res_len=20, callback=None):
		return (['new', 'generated', 'reply'],)
