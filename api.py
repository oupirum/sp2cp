import re
from html.parser import HTMLParser
import requests
from transliterate import translit
import os

def get_threads(board, passcode=''):
	threads = request_json('https://2ch.hk/' + board + '/threads.json', passcode)
	thread_ids = list(map(
		lambda thread: str(thread['num']),
		threads['threads']
	))
	return thread_ids

def get_thread_posts(board, thread_id, passcode=''):
	thread = request_json('https://2ch.hk/' + board + '/res/' + thread_id + '.json', passcode)
	posts = list(map(
		lambda post: Post(str(post['num']), post['comment']),
		thread['threads'][0]['posts']
	))

	for post in posts:
		post.comment, post.reply_to = parse_post_html(post.comment)

	posts = list(filter(
		lambda post: post.comment,
		posts
	))

	return posts

def request_json(url, passcode):
	response = requests.get(
		url,
		cookies={
			'passcode_auth': passcode,
		},
	)

	if response.status_code != 200:
		response.raise_for_status()

	return response.json()

def parse_post_html(post_html):
	parser = PostHTMLParser()
	parser.feed('<span>' + post_html + '</span>')
	post_text = parser.post

	post_lines = list(map(
		lambda line: line.strip(),
		post_text.split('\n')
	))
	post_lines = list(filter(
		lambda line: len(line) > 0,
		post_lines
	))
	return ('\n'.join(post_lines), parser.reply_to)


class Post:
	def __init__(self, id, comment, reply_to=()):
		self.id = id
		self.comment = comment
		self.reply_to = reply_to

	def __repr__(self):
		return '<Post %s %s \'%s\'>' % (self.id, self.reply_to, self.comment)


class PostHTMLParser(HTMLParser):
	def __init__(self):
		super().__init__()
		self._in_reply_link = False
		self.post = ''
		self.reply_to = []

	def handle_starttag(self, tag, attrs):
		attrs = {attr[0]: attr[1] for attr in attrs}
		if tag == 'a' and 'class' in attrs and attrs['class'] == 'post-reply-link':
			self._in_reply_link = True
			self.reply_to.append(attrs['data-num'])
		if tag == 'br':
			self.post += '\n'

	def handle_data(self, data):
		if self._in_reply_link:
			return

		data = re.sub('\s+', ' ', data)

		if len(data.strip()) < 2:
			return

		self.post += data

	def handle_endtag(self, tag):
		if tag == 'a' and self._in_reply_link:
			self._in_reply_link = False


def post(comment, thread_id, board, passcode, pic_file=None):
	thread_url = 'https://2ch.hk/%s/res/%s.html' \
			% (board, thread_id)
	formdata = {
		'task': (None, 'post'),
		'board': (None, board),
		'thread': (None, thread_id),
		'comment': (None, comment),
		'email': (None, ''),
		'usercode': (None, passcode),
		'code': (None, ''),
		'captcha_type': (None, 'invisible_recaptcha'),
		'oekaki_image': (None, ''),
		'oekaki_metadata': (None, ''),
	}
	if pic_file:
		pic_name = translit(
			os.path.basename(pic_file),
			'ru',
			reversed=True
		)
		formdata['formimages[]'] = (pic_name, open(pic_file, 'rb'))

	response = requests.post(
		'https://2ch.hk/makaba/posting.fcgi?json=1',
		files=formdata,
		cookies={
			'passcode_auth': passcode,
		},
		headers={
			'Accept': 'application/json',
			'Cache-Control': 'no-cache',
			'Referer': thread_url,
			'Host': '2ch.hk',
			'Origin': 'https://2ch.hk',
			'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/71.0.3578.98 Safari/537.36',
		})

	if response.status_code != 200:
		response.raise_for_status()

	response_obj = response.json()
	post_id = None
	post_link = None
	if not response_obj['Error']:
		post_id = str(response_obj['Num'])
		post_link = thread_url + '#' + post_id

	return (response_obj, post_id, post_link)
