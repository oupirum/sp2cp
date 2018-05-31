import argparse
import json
import os
import numpy as np
from tensorflow.python.keras.preprocessing.sequence import pad_sequences
from model import create_model
from tensorflow.python.keras.callbacks import Callback, ModelCheckpoint
from tensorflow.python.keras.models import load_model

def main():
	os.makedirs(OPTS.models_dir, exist_ok=True)

	with open(os.path.join(OPTS.input_dir, 'sequences.json'), 'r') as f:
		sequences = json.loads(f.read())

	with open(os.path.join(OPTS.input_dir, 'id2token.json'), 'rb') as f:
		id2token = json.loads(f.read().decode('utf-8'))

		with open(os.path.join(OPTS.models_dir, 'id2token.json'), 'wb') as fw:
			f.seek(0)
			fw.write(f.read())

	print('lexicon:', len(id2token))
	print('sequences:', len(sequences))
	seq_max_len = max([len(seq) for seq in sequences])
	print('seq_max_len:', seq_max_len)
	seq_min_len = min([len(seq) for seq in sequences])
	print('seq_min_len:', seq_min_len)

	data_len = len(sequences) - len(sequences) % OPTS.batch_size
	data = sequences[0:data_len]
	data = pad_sequences(data, maxlen=seq_max_len, dtype='int32')

	model = create_model(
			seq_len=data.shape[-1],
			n_input_nodes=len(id2token),
			batch_size=OPTS.batch_size)

	ckpt_file = os.path.join(OPTS.models_dir, 'ckpt.h5')
	if os.path.exists(ckpt_file):
		model = load_model(ckpt_file)

	x = data
	y = np.roll(x, -1, 1)
	y = y[:, :, None]

	save_step_callback = SaveStepCallback(
			model, save_every_batch=OPTS.save_every_batch)
	ckpt_callback = ModelCheckpoint(
			ckpt_file, monitor='loss', verbose=1, save_best_only=True, mode='min')
	model.fit(
			x=x, y=y,
			epochs=OPTS.epochs,
			batch_size=OPTS.batch_size,
			callbacks=[save_step_callback, ckpt_callback],
			shuffle=True)

	model.save_weights(os.path.join(OPTS.models_dir, 'weights.h5'))


class SaveStepCallback(Callback):
	def __init__(self, model, save_every_batch):
		super(SaveStepCallback, self).__init__()
		self._model = model
		self._save_every = save_every_batch

	def on_epoch_begin(self, epoch, logs={}):
		self._epoch = epoch

	def on_batch_end(self, batch, logs={}):
		step = (self._epoch + 1) * (batch + 1)
		if step % self._save_every == 0:
			weights_file = os.path.join(
					OPTS.models_dir,
					'weights_e%d_b%d.h5' % (self._epoch, batch))
			print('save weights:', weights_file)
			self._model.save_weights(weights_file)

			loss_file = os.path.join(
					OPTS.models_dir,
					'loss_e%d_b%d_%.4f.txt' % (self._epoch, batch, logs.get('loss')))
			open(loss_file, 'w').close()


if __name__ == '__main__':
	parser = argparse.ArgumentParser()
	parser.add_argument(
			'--input_dir',
			type=str,
			default='./dataset/parsed/',
			help='Directory containing sequences and lexicon generated by parse_dataset.py')
	parser.add_argument(
			'--models_dir',
			type=str,
			default='./models/')
	parser.add_argument(
			'--epochs',
			type=int,
			default=20)
	parser.add_argument(
			'--batch_size',
			type=int,
			default=100)
	parser.add_argument(
			'--save_every_batch',
			type=int,
			default=100)
	OPTS = parser.parse_args()

	main()
