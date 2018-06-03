import argparse
import json
import numpy as np
from model import create_model
from parse_dataset import parse_threads, filter_short_threads, \
		split_to_line_sequences
from tensorflow.python.keras import backend as backend

def main():
	threads = parse_threads(OPTS.test_data_dir)
	threads = filter_short_threads(threads, 100)
	sequences, tokens_count = split_to_line_sequences(threads, 150, 10)
	print('sequences:', len(sequences))
	generate(OPTS.weights_file, OPTS.id2token_file, sequences)

def generate(weights_file, id2token_file, seeds, min_res_len=3):
	model, id2token = load_model(weights_file, id2token_file)
	token2id = {token: id for id, token in enumerate(id2token)}

	results = []
	for seed_tokens in seeds:
		seed_ids = [token2id[token] if token in token2id else token2id['<unk>'] \
				for token in seed_tokens]
		res = gen_seq(model, seed_ids, min_res_len)
		res_tokens = [id2token[id] for id in res]
		results.append(res_tokens)
		print(' '.join(seed_tokens))
		print('>>>>>>', ' '.join(res_tokens))
		print('')

	backend.clear_session()
	return results

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

def gen_seq(model, seed, min_len,
		end_tokens=[3],
		forbidden_tokens=[1]):
	generated = []

	for id in seed:
		ni_prob = model.predict(np.array(id)[None, None])[0, 0]

	while True:
		ni_prob /= ni_prob.sum()
		next_id = np.random.choice(a=ni_prob.shape[-1], p=ni_prob)
		generated.append(next_id)
		if len(generated) >= min_len and next_id in end_tokens:
			break

		if next_id in forbidden_tokens:
			model.reset_states()
			return gen_seq(model, seed, min_len, end_tokens, forbidden_tokens)

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
