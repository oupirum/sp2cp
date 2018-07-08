import argparse
import json
import numpy as np
from model import create_model
from parse_dataset import parse_comment_pairs
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
		sequences.extend(parse_comment_pairs(content, 8, 100))

	print('sequences:', len(sequences))
	Generator(OPTS.weights_file, OPTS.id2token_file).generate(
			sequences,
			max_res_len=OPTS.max_res_len)


class Generator:
	def __init__(self, weights_file, id2token_file):
		self._model, self._id2token = self._load_model(weights_file, id2token_file)
		self._token2id = {token: id for id, token in enumerate(self._id2token)}

	def generate(self, seeds,
			min_res_len=3, max_res_len=30,
			callback=None):
		results = []
		for i, seed_tokens in enumerate(seeds):
			seed_ids = [self._token2id[token] if token in self._token2id else self._token2id['<unk>'] \
					for token in seed_tokens]
			res = self._gen_seq(seed_ids,
					min_res_len, max_res_len,
					end_tokens=[self._token2id['<eoc>']],
					forbidden_tokens=[self._token2id['<unk>']])
			res_tokens = [self._id2token[id] for id in res]
			results.append(res_tokens)

			if callback:
				callback(i, res_tokens)
			else:
				print('')
				print(' '.join(seed_tokens))
				print('>>>>>>', ' '.join(res_tokens))

		return results

	def _load_model(self, weights_file, id2token_file):
		with open(id2token_file, 'rb') as f:
			id2token = json.loads(f.read().decode('utf-8'))

		model = create_model(
				seq_len=1,
				n_input_nodes=len(id2token),
				batch_size=1,
				stateful=True)
		model.load_weights(weights_file)

		return (model, id2token)

	def _gen_seq(self, seed,
			min_len, max_len,
			end_tokens,
			forbidden_tokens):
		generated = []

		for id in seed:
			ni_prob = self._model.predict(np.array(id)[None, None])[0, 0]

		while True:
			ni_prob /= ni_prob.sum()
			next_id = np.random.choice(a=ni_prob.shape[-1], p=ni_prob)
			generated.append(next_id)
			if len(generated) >= min_len and next_id in end_tokens:
				break

			if next_id in forbidden_tokens:
				self._model.reset_states()
				return self._gen_seq(seed, min_len, max_len, end_tokens, forbidden_tokens)

			ni_prob = self._model.predict(np.array(next_id)[None, None])[0, 0]

		self._model.reset_states()

		if len(generated) > max_len:
			return self._gen_seq(seed, min_len, max_len, end_tokens, forbidden_tokens)

		return generated


if __name__ == '__main__':
	parser = argparse.ArgumentParser()
	parser.add_argument(
			'--weights_file',
			type=str,
			default='./models/weights.h5')
	parser.add_argument(
			'--id2token_file',
			type=str,
			default='./models/id2token.json')
	parser.add_argument(
			'--test_data_dir',
			type=str,
			default='./tests/dataset/threads/')
	parser.add_argument(
			'--max_res_len',
			type=int,
			default=100)
	OPTS = parser.parse_args()

	main()
