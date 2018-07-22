import time
import pytest
import json
import re
import grub_threads
import autoposter
from autoposter import select_threads, comment_to_tokens, Poster
from grub_threads import Post

class TestAutoposter:

	@pytest.fixture(autouse=True)
	def fake_opts(self, monkeypatch):
		monkeypatch.setattr(autoposter, 'OPTS', OptsFake())

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
		def request_json_fake(url):
			with open('./tests/thread.json', 'rb') as f:
				return f.read().decode('utf-8')
		monkeypatch.setattr(grub_threads, 'request_json', request_json_fake)

	def fake_poster(self, monkeypatch, posted_id, error=None):
		monkeypatch.setattr(autoposter, 'generator', GeneratorFake())

		poster = Poster('some comment', None, '222', Post('111', 'qweqwe'))
		poster._error = error

		def post_fake(*args, **kwargs):
			print(args, kwargs)
			return {'Num': posted_id, 'Error': poster._error, 'Status': 'OK'}
		monkeypatch.setattr(poster, '_post', post_fake)

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
		assert(out == '() {}\n\n<Post 111 [] \'qweqwe\'>\n>>111\nsome comment\nhttps://2ch.hk/b/res/222.html#123\n')

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
		assert(out.endswith('<Post 111 [] \'qweqwe\'>\n>>111\nsome comment\nhttps://2ch.hk/b/res/222.html#123\n'))

		err = capsys.readouterr().err
		assert(err == '')

	def test_poster_got_reply(self, monkeypatch, fake_request_for_replies, capsys):
		poster = self.fake_poster(monkeypatch, 175409951)
		poster.start()
		time.sleep(0.03)
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
		assert(thread_id == '222')
		assert(reply_to.id == '175410055')
		assert(reply_to.comment == 'Какаю бабочками, писаю радугой. Ты просто за ручку не держался, поэтому не в курсе.')


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
	def generate(self, seeds, forbidden_tokens=(), min_res_len=3, max_res_len=20, callback=None):
		return (['new', 'generated', 'reply'],)
