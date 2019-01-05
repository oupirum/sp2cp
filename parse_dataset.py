import argparse
import json
import os
import re
from collections import Counter
from parse_utils import comment_to_tokens

def main():
	os.makedirs(OPTS.out_dir, exist_ok=True)
	sequences_file = os.path.join(OPTS.out_dir, 'sequences.json')
	id2token_file = os.path.join(OPTS.out_dir, 'id2token.json')
	lexicon_file = os.path.join(OPTS.out_dir, 'lexicon.txt')

	sequences, id2token, tokens_count = parse_dataset(
		OPTS.dataset_dir,
		lexicon_limit=OPTS.lexicon_limit,
		seq_min_len=OPTS.sequence_min_len,
		seq_max_len=OPTS.sequence_max_len
	)

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

	tokens_count = collect_lexicon(pairs)
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

def collect_lexicon(pairs):
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
					for token in pair]
		)

	return pairs_ids


if __name__ == '__main__':
	parser = argparse.ArgumentParser()
	parser.add_argument(
		'--dataset_dir',
		type=str,
		default='./dataset/threads/'
	)
	parser.add_argument(
		'--out_dir',
		type=str,
		default='./dataset/parsed/'
	)
	parser.add_argument(
		'--lexicon_limit',
		type=int,
		required=True,
		help='How many most often words use to train (others will be unknown)'
	)
	parser.add_argument(
		'--sequence_min_len',
		type=int,
		default=8,
		help='Min length of the pair of comments (words)'
	)
	parser.add_argument(
		'--sequence_max_len',
		type=int,
		default=100,
		help='Max length of the pair of comments (words)'
	)
	OPTS = parser.parse_args()

	main()
