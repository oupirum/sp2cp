import argparse
import json
import os
import random
import re
from collections import Counter

def main():
	os.makedirs(OPTS.out_dir, exist_ok=True)
	sequences_file = os.path.join(OPTS.out_dir, 'sequences.json')
	id2token_file = os.path.join(OPTS.out_dir, 'id2token.json')
	lexicon_file = os.path.join(OPTS.out_dir, 'lexicon.txt')

	sequences, id2token, tokens_count = parse_dataset(
			OPTS.dataset_dir,
			lexicon_limit=OPTS.lexicon_limit,
			seq_max_len=OPTS.sequence_len,
			split=OPTS.split)

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

def parse_dataset(ds_dir, lexicon_limit, seq_max_len=100, seq_min_len=5, split='line'):
	id2token = [
		'<pad>',
		'<unk>',
		'<eol>',
		'<eoc>',
		'<n>',
	]
	token2id = {v: i for i, v in enumerate(id2token)}

	threads = parse_threads(ds_dir)
	threads = filter_short_threads(threads, seq_max_len)
	print('threads:', len(threads))

	if split == 'line':
		sequences, tokens_count = split_to_line_sequences(threads, seq_max_len, seq_min_len)
	elif split == 'comment':
		sequences, tokens_count = split_to_comment_sequences(threads, seq_max_len, seq_min_len)
	else:
		sequences, tokens_count = split_to_plain_sequences(threads, seq_max_len)
	print('sequences:', len(sequences))

	for tc in tokens_count.most_common(lexicon_limit):
		token = tc[0]
		if token not in token2id:
			id2token.append(token)
			token2id[token] = len(token2id)
	print('lexicon:', len(id2token))

	seqs_ids = sequences_ids(sequences, id2token)

	return (seqs_ids, id2token, dict(tokens_count))

def parse_threads(ds_dir):
	threads = []

	files = os.listdir(ds_dir)
	random.shuffle(files)
	for i in range(len(files)):
		file = files[i]
		if not re.match('\d+\.txt', file):
			continue

		print(i, '============================ ' + file + ' ==============================')
		with open(os.path.join(ds_dir, file), 'rb') as f:
			content = f.read().decode('utf-8')
			lines = content.split('\n')
		print(lines[0])

		thread = []
		for line in lines:
			line = line.strip()
			line = line.lower()
			if line:
				line_tokens = str_to_tokens(line)
				if line_tokens:
					for token in line_tokens:
						thread.append(token)
					thread.append('<eol>')
			else:
				if thread and thread[-1] != '<eoc>':
					thread.append('<eoc>')
		if thread:
			threads.append(thread)

	return threads

def str_to_tokens(s):
	tokens = []
	for token in s.split(' '):
		process_token(token, tokens)
	return tokens

def filter_short_threads(threads, min_len):
	threads = list(filter(
			lambda thread: len(list(filter(
					lambda token: token == '<eoc>',
					thread))) >= 5,
			threads))
	threads = list(filter(
			lambda thread: len(thread) >= min_len,
			threads))
	return threads

def split_to_comment_sequences(threads, seq_max_len, seq_min_len):
	lexicon = Counter()

	sequences = []
	comment = []
	for thread in threads:
		for token in thread:
			comment.append(token)
			if token == '<eoc>':
				if comment \
						and len(comment) <= seq_max_len \
						and len(comment) >= seq_min_len:
					sequences.append(comment)
					lexicon.update(comment)
				comment = []

	return (sequences, lexicon)

def split_to_line_sequences(threads, seq_max_len, seq_min_len):
	lexicon = Counter()

	sequences = []
	for thread in threads:
		lines = []
		line = []
		for token in thread:
			if token == '<eoc>':
				lines[-1].append(token)
				continue
			line.append(token)
			if token == '<eol>':
				lines.append(line)
				line = []
		seq = []
		for line in lines:
			if len(line) < seq_min_len:
				continue
			if len(seq) + len(line) > seq_max_len:
				if seq:
					sequences.append(seq)
					lexicon.update(seq)
				seq = []
				if len(line) <= seq_max_len:
					seq.extend(line)
			else:
				seq.extend(line)
		if seq:
			sequences.append(seq)
			lexicon.update(seq)

	return (sequences, lexicon)

def split_to_plain_sequences(threads, seq_len):
	lexicon = Counter()

	sequences = []
	for thread in threads:
		end = len(thread) - len(thread) % seq_len
		for i in range(0, end, seq_len):
			seq = thread[i:i+seq_len]
			sequences.append(seq)
			lexicon.update(seq)

	return (sequences, lexicon)

def sequences_ids(sequences, id2token):
	token2id = {token: id for id, token in enumerate(id2token)}
	seqs_ids = []

	for sequence in sequences:
		seqs_ids.append(
				[token2id[token] if token in token2id else token2id['<unk>'] \
						for token in sequence])

	return seqs_ids

def process_token(token, tokens):
	token = token.strip()
	token = re.sub('^[0-9]+[).:]$', '', token)
	if not token:
		return False
	if not re.search('[a-zа-яё0-9:\-()^_=]', token):
		return False

	if re.fullmatch('[a-z0-9.\-]+@[a-z0-9.\-]+', token):
		tokens.append('ti.hui@i.pidor.com')
		return True
	if token == '(нет)':
		tokens.append(token)
		return True
	if re.fullmatch('т\.[еодп]\.?', token):
		tokens.append(re.sub('\.?$', '.', token))
		return True
	if re.fullmatch('([0-9]+-?[0-9]*)?т\.р\.?', token):
		if re.match('[0-9]', token):
			tokens.append('<n>т.р.')
		else:
			tokens.append('т.р.')
		return True
	if re.fullmatch('[0-9]+-(ой|ая|ый|й|я|х)', token):
		tokens.append(re.sub('^[0-9]+-(ой|ая|ый|й|я|х|м|му)$', '<n>-\\1', token))
		return True
	if re.fullmatch('[0-9]+([\-+.]+[0-9]+)*[a-zа-яё]*', token):
		tokens.append('<n>')
		return True

	token = re.sub('[\'"«»“”]+', '', token)
	token = re.sub('(\\\\t)+', '', token)
	token = re.sub('</?[a-z]+>', '', token)

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

	if re.fullmatch('.*?\)+0+[)0]*', token):
		process_token(re.sub('\)+0+[)0]*$', '', token), tokens)
		tokens.append('))0')
		return True

	if re.fullmatch('.*?\(+9+[(9]*', token):
		process_token(re.sub('\(+9+[(9]*$', '', token), tokens)
		tokens.append('((9')
		return True

	if re.fullmatch('.*?!+1+[!1]*', token):
		process_token(re.sub('!+1+[!1]*$', '', token), tokens)
		tokens.append('!!11')
		return True

	if re.fullmatch('.*?([a-zа-яё])1{3,}', token):
		process_token(re.sub('1{3,}$', '', token), tokens)
		tokens.append('111')
		return True

	if re.search('-+>+', token):
		sts = re.split('-+>+', token)
		for i, st in enumerate(sts):
			if process_token(st, tokens) and i < len(sts) - 1:
				tokens.append('->')
		return True

	for char in ['.', ',', '!', '?', '(', ')']:
		if re.fullmatch('.*?' + re.escape(char) + '{2,}', token):
			process_token(re.sub(re.escape(char) + '{2,}$', '', token), tokens)
			tokens.append(char * 3)
			return True

	for char in ['.', ',', '!', '?', ':', ';', '-', '–', '*', '=', '~', '$']:
		if re.fullmatch('.*?' + re.escape(char), token):
			process_token(re.sub(re.escape(char) + '$', '', token), tokens)
			tokens.append(char)
			return True

	for char in ['.', ',', '!', '?', ':', ';', '-', '–', '*', '=', '~', '$']:
		if re.fullmatch(re.escape(char) + '.*', token):
			tokens.append(char)
			process_token(re.sub('^' + re.escape(char), '', token), tokens)
			return True

	for char in ['.', ',', '!', '?', ':', ';', '+', '*', '=']:
		if re.search(re.escape(char), token):
			sts = re.split(re.escape(char), token)
			for i, st in enumerate(sts):
				if process_token(st, tokens) and i < len(sts) - 1:
					tokens.append(char)
			return True

	if re.fullmatch('\(([a-zа-яё0-9]).*', token):
		process_token(re.sub('^\(', '', token), tokens)
		return True
	if re.fullmatch('.*?([a-zа-яё0-9])\)', token):
		process_token(re.sub('\)$', '', token), tokens)
		return True

	if re.search('[()]', token):
		for st in re.split('[()]', token):
			process_token(st, tokens)
		return True

	if re.fullmatch('>+([a-zа-яё0-9]).*', token):
		tokens.append('>')
		process_token(re.sub('^>+', '', token), tokens)
		return True

	if re.search('([.,!?;])-', token):
		sws = re.sub('([a-zа-яё0-9])([.,!?;])-([a-zа-яё0-9])', '\\1 \\2 - \\3', token)
		for sw in sws:
			process_token(sw, tokens)
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
			'--split',
			type=str,
			default='line',
			help='How to split dataset to sequences: "line", "comment" or "plain"')
	parser.add_argument(
			'--sequence_len',
			type=int,
			default=100,
			help="Max length of the sequence")
	OPTS = parser.parse_args()

	main()
