import json
import numpy as np
from model import create_model

class Generator:
	def __init__(self, weights_file, id2token_file):
		self._model, self._id2token = self._load_model(weights_file, id2token_file)
		self._token2id = {token: id for id, token in enumerate(self._id2token)}

	def generate(self,
		seeds,
		forbidden_tokens=(),
		min_res_len=3, max_res_len=30,
		callback=None
	):
		results = []
		forbidden_ids = [self._token2id[token] if token in self._token2id else self._token2id['<unk>'] \
				for token in forbidden_tokens]
		for i, seed_tokens in enumerate(seeds):
			seed_ids = [self._token2id[token] if token in self._token2id else self._token2id['<unk>'] \
					for token in seed_tokens]
			res = self._gen_seq(
				seed_ids,
				min_res_len, max_res_len,
				end_tokens=[self._token2id['<eoc>']],
				forbidden_ids=forbidden_ids
			)
			res_tokens = [self._id2token[id] for id in res]
			results.append(res_tokens)

			if callback:
				callback(i, res_tokens, seed_tokens)

		return results

	def _load_model(self, weights_file, id2token_file):
		with open(id2token_file, 'rb') as f:
			id2token = json.loads(f.read().decode('utf-8'))

		model = create_model(
			seq_len=1,
			n_input_nodes=len(id2token),
			batch_size=1,
			stateful=True
		)
		model.load_weights(weights_file)

		return (model, id2token)

	def _gen_seq(self,
		seed,
		min_len, max_len,
		end_tokens,
		forbidden_ids
	):
		generated = []

		for id in seed:
			ni_prob = self._model.predict(np.array(id)[None, None])[0, 0]

		while True:
			ni_prob /= ni_prob.sum()
			next_id = np.random.choice(a=ni_prob.shape[-1], p=ni_prob)
			generated.append(next_id)
			if len(generated) >= min_len and next_id in end_tokens:
				break

			if next_id in forbidden_ids:
				self._model.reset_states()
				return self._gen_seq(seed, min_len, max_len, end_tokens, forbidden_ids)

			ni_prob = self._model.predict(np.array(next_id)[None, None])[0, 0]

		self._model.reset_states()

		if len(generated) > max_len:
			return self._gen_seq(seed, min_len, max_len, end_tokens, forbidden_ids)

		return generated
