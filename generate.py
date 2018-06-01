import argparse
import os
import json
import re
import numpy as np
from model import create_model
from parse_dataset import str_to_tokens

def main():
	comments = []
	files = os.listdir(OPTS.test_data_dir)
	for file in files:
		if not re.fullmatch('\d+\.txt', file):
			continue
		with open(os.path.join(OPTS.test_data_dir, file), 'rb') as f:
			thread_str = f.read().decode('utf-8')
			thread_comments = thread_str.split('\n\n')
			thread_comments = list(filter(lambda tc: tc, thread_comments))
			comments.extend(thread_comments)

	generate(OPTS.weights_file, OPTS.id2token_file, comments)

def generate(weights_file, id2token_file, seed, min_len=100):
	model, id2token = load_model(weights_file, id2token_file)
	token2id = {token: id for id, token in enumerate(id2token)}

	if not isinstance(seed, list):
		seed = [seed]

	res_tokens = []
	for seed_str in seed:
		seed_tokens = str_to_tokens(seed_str)
		seed_ids = [token2id[token] if token in token2id else token2id['<unk>'] \
			for token in seed_tokens]

		res = gen_seq(model, seed_ids, min_len)
		res_tokens = [id2token[id] for id in res]
		print('')
		print(seed_str)
		print('>>>', ' '.join(res_tokens))

	return res_tokens

def load_model(weights_file, id2token_file):
	with open(id2token_file, 'rb') as f:
		id2token = json.loads(f.read().decode('utf-8'))

	model = create_model(
			seq_len=1,
			n_input_nodes=len(id2token),
			batch_size=1,
			stateful=True)
	model.load_weights(weights_file)

	return (model, id2token)

def gen_seq(model, seed, min_len):
	generated = []
	end_tokens = [2]

	for id in seed:
		ni_prob = model.predict(np.array(id)[None, None])[0, 0]

	while True:
		# TODO: ValueError: probabilities do not sum to 1
		next_id = np.random.choice(a=ni_prob.shape[-1], p=ni_prob)
		generated.append(next_id)
		if len(generated) > min_len and next_id in end_tokens:
			break
		ni_prob = model.predict(np.array(next_id)[None, None])[0, 0]

	model.reset_states()

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
	OPTS = parser.parse_args()

	main()
