import argparse
from generator import Generator
from parse_dataset import comment_to_tokens
import os
import re

def main():
	sequences = []

	files = os.listdir(OPTS.test_data_dir)
	files.sort()
	for i in range(len(files)):
		file = files[i]
		if not re.match('\d+\.txt', file):
			continue

		with open(os.path.join(OPTS.test_data_dir, file), 'rb') as f:
			content = f.read().decode('utf-8')
		for comment in content.split('\n\n'):
			tokens = comment_to_tokens(comment)
			if len(tokens) >= 10 and len(tokens) <= 80:
				sequences.append(tokens)

	def callback(i, res_tokens, seed_tokens):
		print('')
		print(' '.join(seed_tokens))
		print('>>>>>>', ' '.join(res_tokens))

	print('sequences:', len(sequences))
	Generator(OPTS.weights_file, OPTS.id2token_file).generate(
		sequences,
		forbidden_tokens=OPTS.forbidden_tokens.split(',') if OPTS.forbidden_tokens else (),
		max_res_len=OPTS.max_res_len,
		callback=callback
	)


if __name__ == '__main__':
	parser = argparse.ArgumentParser()
	parser.add_argument(
		'--weights_file',
		type=str,
		default='./models/weights.h5'
	)
	parser.add_argument(
		'--id2token_file',
		type=str,
		default='./models/id2token.json'
	)
	parser.add_argument(
		'--test_data_dir',
		type=str,
		default='./tests/dataset/threads/'
	)
	parser.add_argument(
		'--forbidden_tokens',
		type=str,
		default='<unk>'
	)
	parser.add_argument(
		'--max_res_len',
		type=int,
		default=200
	)
	OPTS = parser.parse_args()

	main()
