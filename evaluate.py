import sys
import json
import numpy as np
from model import create_model
from parse_dataset import parse_tokens, split_to_plain_sequences, \
	tokens_to_ids

ds = sys.argv[1]
models_dir = './models/' + ds + '/'
weights_file = sys.argv[2] if len(sys.argv) > 2 else 'weights.h5'
ds_dir = './dataset/threads_test/'

def main():
	with open(models_dir + 'id2token.json', 'rb') as f:
		id2token = json.loads(f.read().decode('utf-8'))
		token2id = {token: id for id, token in enumerate(id2token)}

	threads = parse_tokens(ds_dir)
	print('threads:', len(threads))
	sequences, _ = split_to_plain_sequences(threads, 100)
	print('sequences:', len(sequences))
	data_test = tokens_to_ids(sequences, token2id)

	model = create_model(
			seq_len=1,
			n_input_nodes=len(id2token),
			batch_size=1,
			stateful=True)
	model.load_weights(models_dir + weights_file)

	evaluate(model, data_test, id2token)

def evaluate(model, seqs, id2token):
	results = ''
	for seed_seq in seqs:
		res = generate(model, seed_seq)
		result = '\n' \
				+ ' '.join([id2token[id] for id in seed_seq]) + '\n' \
				+ '>>>' + ' '.join([id2token[id] for id in res]) + '\n'
		print(result)
		results += result

	with open(models_dir + 'results.txt', 'w') as f:
		f.write(results)

def generate(model, seed):
	generated = []
	end_tokens = [2]

	for id in seed:
		ni_prob = model.predict(np.array(id)[None, None])[0, 0]

	while True:
		next_id = np.random.choice(a=ni_prob.shape[-1], p=ni_prob)
		generated.append(next_id)
		if len(generated) > 100 and next_id in end_tokens:
			break
		ni_prob = model.predict(np.array(next_id)[None, None])[0, 0]

	model.reset_states()

	return generated


if __name__ == '__main__':
	main()
