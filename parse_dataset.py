import argparse
import json
import os
import re
from collections import Counter
from fix_typos import fix_typos

def main():
	os.makedirs(OPTS.out_dir, exist_ok=True)
	sequences_file = os.path.join(OPTS.out_dir, 'sequences.json')
	id2token_file = os.path.join(OPTS.out_dir, 'id2token.json')
	lexicon_file = os.path.join(OPTS.out_dir, 'lexicon.txt')

	sequences, id2token, tokens_count = parse_dataset(
			OPTS.dataset_dir,
			lexicon_limit=OPTS.lexicon_limit,
			seq_min_len=OPTS.sequence_min_len,
			seq_max_len=OPTS.sequence_max_len)

	with open(sequences_file, 'w') as f:
		f.write(json.dumps(sequences))

	with open(id2token_file, 'wb') as f:
		f.write(json.dumps(id2token, ensure_ascii=False).encode('utf-8'))

	tcs = list(tokens_count.items())
	tcs.sort(key=lambda tc: tc[1])
	with open(lexicon_file, 'wb') as f:
		f.write('\n'.join([t + ' ' + str(c) for t, c in tcs]).encode('utf-8'))

	print('')
	print('tokens count:')
	print('>= 1', len(tcs))
	print('>= 2', len(list(filter(lambda tc: tc[1] >= 2, tcs))))
	print('>= 3', len(list(filter(lambda tc: tc[1] >= 3, tcs))))
	print('>= 4', len(list(filter(lambda tc: tc[1] >= 4, tcs))))

def parse_dataset(ds_dir, lexicon_limit, seq_min_len, seq_max_len):
	id2token = [
		'<pad>',
		'<unk>',
		'<eol>',
		'<eoc>',
		'<n>',
	]
	token2id = {v: i for i, v in enumerate(id2token)}

	pairs = []
	files = os.listdir(ds_dir)
	files.sort()
	for i in range(len(files)):
		file = files[i]
		if not re.match('\d+\.txt', file):
			continue

		with open(os.path.join(ds_dir, file), 'rb') as f:
			content = f.read().decode('utf-8')

		t_pairs = parse_comment_pairs(content, seq_min_len, seq_max_len)
		pairs.extend(t_pairs)

		print(i, '============================ ' + file + ' ==============================')
		for pair in t_pairs:
			print(' '.join(pair))
			print('')
	print('sequences:', len(pairs))

	tokens_count = get_lexicon(pairs)
	for tc in tokens_count.most_common(lexicon_limit):
		token = tc[0]
		if token not in token2id:
			id2token.append(token)
			token2id[token] = len(token2id)
	print('lexicon:', len(id2token))

	pairs_ids = tokens_to_ids(pairs, id2token)

	return (pairs_ids, id2token, dict(tokens_count))

def parse_comment_pairs(thread_content, min_len, max_len):
	tokens = []
	pairs = thread_to_comment_pairs(thread_content)
	for pair in pairs:
		if len(' '.join(pair).split(' ')) > max_len:
			continue
		c1 = comment_to_tokens(pair[0])
		c2 = None
		if c1:
			c2 = comment_to_tokens(pair[1])
		if c1 and c2:
			l = len(c1) + len(c2)
			if l >= min_len and l <= max_len:
				pair_tokens = c1
				pair_tokens.extend(c2)
				tokens.append(pair_tokens)
	return tokens

def thread_to_comment_pairs(thread_content):
	pairs = []
	comments = thread_content.split('\n\n')
	for i in range(0, len(comments) - 1, 2):
		pairs.append((comments[i], comments[i + 1]))
	return pairs

def comment_to_tokens(comment):
	tokens = []
	lines = comment.split('\n')
	for line in lines:
		line = line.strip()
		if line:
			line = line.lower()
			line = fix_typos(line)
			line_tokens = str_to_tokens(line)
			if line_tokens:
				tokens.extend(line_tokens)
				tokens.append('<eol>')
	if tokens and tokens[-1] != '<eoc>':
		tokens.append('<eoc>')
	return tokens

def str_to_tokens(s):
	tokens = []
	for token in s.split(' '):
		process_token(token, tokens)
	return tokens

def get_lexicon(pairs):
	lexicon = Counter()
	for pair_tokens in pairs:
		lexicon.update(pair_tokens)
	return lexicon

def tokens_to_ids(pairs, id2token):
	token2id = {token: id for id, token in enumerate(id2token)}
	pairs_ids = []

	for pair in pairs:
		pairs_ids.append(
				[token2id[token] if token in token2id else token2id['<unk>'] \
						for token in pair])

	return pairs_ids

def process_token(token, tokens):
	token = token.strip()
	if not token:
		return False

	token = token.strip()
	if not token:
		return False
	if not re.search('[a-zа-яё0-9\-_–:()^=>$/]', token):
		return False

	if re.match('>+.', token):
		tokens.append('>')
		return process_token(re.sub('^>+', '', token), tokens)

	if re.fullmatch('[a-z0-9.\-]+@[a-z0-9.\-]+', token):
		tokens.append('ti.hui@i.pidor.com')
		return True
	if token.startswith('chrome://flags'):
		tokens.append(token)
		return True
	if re.fullmatch('(https?://)?[a-z0-9.\-]+\.(com|net|ru|onion|org)/?[a-zа-яё0-9:/\-.?=_#$%]+', token):
		tokens.append(token)
		return True

	if re.fullmatch('т\.[еодп]\.?', token):
		tokens.append(re.sub('\.?$', '.', token))
		return True
	if re.fullmatch('.*?[0-9]*т\.р\.?', token):
		if re.search('[0-9]', token):
			tokens.append('<n>т.р.')
		else:
			tokens.append('т.р.')
		return True
	if token == '9000':
		tokens.append(token)
		return True
	if re.fullmatch('[0-9][\-+.0-9]*', token):
		tokens.append('<n>')
		return True
	if re.match('[0-9][\-+.0-9]*[\-/$]*[a-zа-яё]+', token):
		tokens.append('<n>')
		sts = re.sub('^[\-+.0-9]*[0-9](-?)(\$?)(/?)', '\\1 \\2 \\3 ', token).split(' ')
		for st in sts:
			process_token(st, tokens)
		return True

	if token == '(нет)':
		tokens.append(token)
		return True

	if re.fullmatch('.*?:\)+', token):
		process_token(re.sub(':\)+$', '', token), tokens)
		tokens.append(':)')
		return True
	if re.fullmatch('.*?:\(+', token):
		process_token(re.sub(':\(+$', '', token), tokens)
		tokens.append(':(')
		return True
	if re.fullmatch('.*?:d+', token):
		process_token(re.sub(':d+$', '', token), tokens)
		tokens.append(':d')
		return True
	if re.fullmatch('.*?xd+', token):
		process_token(re.sub('xd+$', '', token), tokens)
		tokens.append('xd')
		return True
	if re.fullmatch('.*?:[3з]', token):
		process_token(re.sub(':[3з]+$', '', token), tokens)
		tokens.append(':3')
		return True
	if re.fullmatch('.*?\^_\^', token):
		process_token(re.sub('\^_\^+$', '', token), tokens)
		tokens.append('^_^')
		return True

	if re.fullmatch('[a-zа-яё]+', token):
		tokens.append(token)
		return True

	if re.fullmatch('.*?\)+0+[)0]*', token):
		process_token(re.sub('\)+0+[)0]*$', '', token), tokens)
		tokens.append('))0')
		return True
	if re.fullmatch('.*?\(+9+[(9]*', token):
		process_token(re.sub('\(+9+[(9]*$', '', token), tokens)
		tokens.append('((9')
		return True
	if re.fullmatch('.*?!*1+[!1]+', token):
		process_token(re.sub('!*1+[!1]+$', '', token), tokens)
		tokens.append('!!11')
		return True
	if re.fullmatch('.*?([a-zа-яё])1{3,}', token):
		process_token(re.sub('1{3,}$', '', token), tokens)
		tokens.append('111')
		return True
	if re.fullmatch('.*?((\?+)?(!+\?+)+)', token):
		process_token(re.sub('(\?+)?(!+\?+)+$', '', token), tokens)
		tokens.append('!?')
		return True

	if re.fullmatch('[a-zа-яё0-9]+', token):
		tokens.append(token)
		return True

	if re.search('-+>+', token):
		sts = re.split('-+>+', token)
		for i, st in enumerate(sts):
			process_token(st, tokens)
			if i < len(sts) - 1:
				tokens.append('->')
		return True

	token = re.sub('-{2,}', '–', token)

	for char in ['.', ',', '!', '?', '(', ')', '-', '_', '+']:
		if re.fullmatch('.*?' + re.escape(char) + '{2,}', token):
			process_token(re.sub(re.escape(char) + '{2,}$', '', token), tokens)
			tokens.append(char * 3)
			return True
	for char in ['.', ',', '!', '?', '(', ')', '-', '_', '+']:
		if re.fullmatch(re.escape(char) + '{2,}.*?', token):
			tokens.append(char * 3)
			return process_token(re.sub('^' + re.escape(char) + '{2,}', '', token), tokens)

	for char in ['.', ',', '!', '?', ':', ';', '-', '–', '*', '=', '~', '$']:
		if re.fullmatch('.*?' + re.escape(char), token):
			process_token(re.sub(re.escape(char) + '$', '', token), tokens)
			tokens.append(char)
			return True
	for char in ['.', ',', '!', '?', ':', ';', '-', '–', '*', '=', '~', '$']:
		if re.fullmatch(re.escape(char) + '.*', token):
			tokens.append(char)
			return process_token(re.sub('^' + re.escape(char), '', token), tokens)

	for char in ['.', ',', '!', '?', ':', ';', '+', '*', '=', '–']:
		if re.search(re.escape(char), token):
			sts = re.split(re.escape(char), token)
			for i, st in enumerate(sts):
				if process_token(st, tokens) and i < len(sts) - 1:
					tokens.append(char)
			return True

	if re.search('[a-zа-яё$]+/[a-zа-яё]+', token):
		sts = token.split('/')
		for i, st in enumerate(sts):
			if process_token(st, tokens) and i < len(sts) - 1:
				tokens.append('/')
		return True

	if re.fullmatch('[(\[\]][a-zа-яё0-9].*', token):
		return process_token(re.sub('^[(\[\]]', '', token), tokens)
	if re.fullmatch('.*?[a-zа-яё0-9][)\[\]]', token):
		return process_token(re.sub('[)\[\]]$', '', token), tokens)

	if re.search('[()]', token):
		for st in re.split('[()]', token):
			process_token(st, tokens)
		return True

	if re.search('[.,!?;]-', token):
		sts = re.sub('([a-zа-яё0-9])([.,!?;])-([a-zа-яё0-9])', '\\1 \\2 - \\3', token).split(' ')
		for st in sts:
			process_token(st, tokens)
		return True

	tokens.append(token)
	return True


if __name__ == '__main__':
	parser = argparse.ArgumentParser()
	parser.add_argument(
			'--dataset_dir',
			type=str,
			default='./dataset/threads/')
	parser.add_argument(
			'--out_dir',
			type=str,
			default='./dataset/parsed/')
	parser.add_argument(
			'--lexicon_limit',
			type=int,
			required=True,
			help='How many most often words use to train (others will be unknown)')
	parser.add_argument(
			'--sequence_min_len',
			type=int,
			default=8,
			help="Min length of the pair of comments (words)")
	parser.add_argument(
			'--sequence_max_len',
			type=int,
			default=100,
			help="Max length of the pair of comments (words)")
	OPTS = parser.parse_args()

	main()
