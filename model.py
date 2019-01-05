from tensorflow.python.keras.layers import Input, Dense, TimeDistributed
from tensorflow.python.keras.layers import Embedding
from tensorflow.python.keras.layers import GRU
from tensorflow.python.keras.models import Model

def create_model(
	seq_len,
	n_input_nodes, n_embedding_nodes=300, n_hidden_nodes=500,
	batch_size=20, stateful=False
):
	input_layer = Input(
		batch_shape=(batch_size, seq_len)
	)

	x = Embedding(
		input_dim=n_input_nodes,
		output_dim=n_embedding_nodes,
		mask_zero=True
	)(input_layer)
	x = GRU(
		n_hidden_nodes,
		return_sequences=True,
		stateful=stateful
	)(x)
	x = GRU(
		n_hidden_nodes,
		return_sequences=True,
		stateful=stateful
	)(x)

	output_layer = TimeDistributed(
		Dense(n_input_nodes, activation="softmax")
	)(x)

	model = Model(inputs=input_layer, outputs=output_layer)
	model.compile(
		loss="sparse_categorical_crossentropy",
		optimizer='adam'
	)

	return model
