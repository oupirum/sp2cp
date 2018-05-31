from parse_dataset import \
		process_token, \
		parse_dataset, \
		split_to_comment_sequences, \
		split_to_line_sequences, \
		split_to_plain_sequences

class TestParseDataset():
	def setup(self):
		print('')

	def test_process_token(self):
		self.pt('qwe@gmail.com', ['ti.hui@i.pidor.com'])
		self.pt('10т.р', ['<n>т.р.'])
		self.pt('т.р.', ['т.р.'])
		self.pt('т.д', ['т.д.'])
		self.pt('100к', ['<n>'])
		self.pt('3.5', ['<n>'])
		self.pt('2-ая', ['<n>-ая'])
		self.pt('"qwe"', ['qwe'])
		self.pt('"qwe"\\t', ['qwe'])
		self.pt('\\t\\t"qwe"\\t', ['qwe'])
		self.pt('qwe<br>', ['qwe'])
		self.pt('qwe:))', ['qwe', ':)'])
		self.pt('qwe:ddd', ['qwe', ':d'])
		self.pt('qwe)xd', ['qwe', 'xd'])
		self.pt('qwe:3', ['qwe', ':3'])
		self.pt('qwe))))00', ['qwe', '))0'])
		self.pt('qwe!!!11!!1!1!', ['qwe', '!!11'])
		self.pt('qwe111111', ['qwe', '111'])
		self.pt('qwe->', ['qwe', '->'])
		self.pt('qwe->123', ['qwe', '->', '<n>'])
		self.pt('qwe!!!!!!!!!!!', ['qwe', '!!!'])
		self.pt('qwe!?', ['qwe', '!', '?'])
		self.pt('-qwe', ['-', 'qwe'])
		self.pt('(qwe)', ['qwe'])
		self.pt('one(two),three', ['one', 'two', ',', 'three'])
		self.pt('one+two+three', ['one', '+', 'two', '+', 'three'])
		self.pt('qwe?-rty', ['qwe', '?', '-', 'rty'])

	def pt(self, token, expect_tokens):
		tokens = []
		process_token(token, tokens)
		assert(tokens == expect_tokens)

	def test_parse_dataset(self):
		ds_dir = './tests/dataset/threads/'
		seqs, id2token, lexicon = parse_dataset(ds_dir, 5000)

		assert(len(seqs) > 0)
		assert(len(seqs[0]) > 0)
		assert(len(seqs[-1]) > 0)

		assert(len(id2token) > 3000)
		assert('<pad>' not in lexicon)
		assert('<unk>' not in lexicon)
		assert('<eol>' in lexicon)
		assert('<eoc>' in lexicon)
		assert(len(id2token) == len(lexicon) + 2)  # words + <pad>, <unk>

	def test_split_to_comment_sequences(self):
		seqs, _ = split_to_comment_sequences([
			[
				'1', '2', '<eol>', '<eoc>',
				'4', '5', '6', '7', '<eol>', '<eoc>',
				'8', '9', '<eol>', '10', '<eol>', '<eoc>',
				'11', '12', '<eol>', '13', '14', '15', '16', '<eol>', '<eoc>'
			],
			[
				'17', '18', '19', '20', '21', '<eol>', '<eoc>',
				'<eol>', '<eoc>',
				'23', '24', '<eol>', '<eoc>'
			]
		], 4, 2)
		assert(seqs == [
			['1', '2', '<eol>', '<eoc>'],
			['<eol>', '<eoc>'],
			['23', '24', '<eol>', '<eoc>']
		])

		seqs, _ = split_to_comment_sequences([
			[
				'1', '2', '<eol>', '<eoc>',
				'4', '5', '6', '7', '<eol>', '<eoc>',
				'8', '9', '<eol>', '10', '<eol>', '<eoc>',
				'11', '12', '<eol>', '13', '14', '15', '16', '<eol>', '<eoc>'
			],
			[
				'17', '18', '19', '20', '21', '<eol>', '<eoc>',
				'22', '<eol>', '<eoc>',
				'23', '24', '<eol>', '<eoc>'
			]
		], 5, 4)
		assert(seqs == [
			['1', '2', '<eol>', '<eoc>'],
			['23', '24', '<eol>', '<eoc>']
		])

		seqs, _ = split_to_comment_sequences([
			[
				'1', '2', '<eol>', '<eoc>',
				'4', '5', '6', '7', '<eol>', '<eoc>',
				'8', '9', '<eol>', '10', '<eol>', '<eoc>',
				'11', '12', '<eol>', '13', '14', '15', '16', '<eol>', '<eoc>'
			],
			[
				'17', '18', '19', '20', '21', '<eol>', '<eoc>',
				'22', '<eol>', '<eoc>',
				'23', '24', '<eol>', '<eoc>'
			]
		], 6, 3)
		assert(seqs == [
			['1', '2', '<eol>', '<eoc>'],
			['4', '5', '6', '7', '<eol>', '<eoc>'],
			['8', '9', '<eol>', '10', '<eol>', '<eoc>'],
			['22', '<eol>', '<eoc>'],
			['23', '24', '<eol>', '<eoc>']
		])

	def test_split_to_line_sequences(self):
		seqs, _ = split_to_line_sequences([
			[
				'1', '2', '<eol>', '<eoc>',
				'4', '5', '6', '7', '<eol>', '<eoc>',
				'8', '9', '<eol>', '10', '<eol>', '<eoc>',
				'11', '12', '<eol>', '13', '14', '15', '16', '<eol>', '<eoc>'
			],
			[
				'18', '19', '20', '21', '22', '<eol>', '<eoc>',
				'23', '<eol>', '<eoc>',
				'24', '25', '<eol>', '<eoc>'
			]
		], 4, 2)
		assert(seqs == [
			['1', '2', '<eol>', '<eoc>'],
			['8', '9', '<eol>'],
			['10', '<eol>', '<eoc>'],
			['11', '12', '<eol>'],
			['23', '<eol>', '<eoc>'],
			['24', '25', '<eol>', '<eoc>']
		])

		seqs, _ = split_to_line_sequences([
			[
				'1', '2', '<eol>', '<eoc>',
				'4', '5', '6', '7', '<eol>', '<eoc>',
				'8', '9', '<eol>', '10', '<eol>', '<eoc>',
				'11', '12', '<eol>', '13', '14', '15', '16', '<eol>', '<eoc>'
			],
			[
				'1', '2', '4', '5', '6', '<eol>', '<eoc>',
				'7', '<eol>', '<eoc>',
				'8', '9', '<eol>', '<eoc>'
			]
		], 5, 4)
		assert(seqs == [
			['1', '2', '<eol>', '<eoc>'],
			['8', '9', '<eol>', '<eoc>']
		])

	def test_split_to_plain_sequences(self):
		seqs, _ = split_to_plain_sequences([
			[
				'1', '2', '<eol>', '<eoc>',
				'4', '5', '6', '7', '<eol>', '<eoc>',
				'8', '9', '<eol>', '10', '<eol>', '<eoc>',
				'11', '12', '<eol>', '13', '14', '15', '16', '<eol>', '<eoc>'
			],
			[
				'1', '<eol>', '<eoc>',
			],
			[
				'18', '19', '20', '21', '22', '<eol>', '<eoc>',
				'23', '<eol>', '<eoc>',
				'24', '25', '<eol>', '<eoc>'
			]
		], 4)
		assert(seqs == [
			['1', '2', '<eol>', '<eoc>'],
			['4', '5', '6', '7'],
			['<eol>', '<eoc>', '8', '9'],
			['<eol>', '10', '<eol>', '<eoc>'],
			['11', '12', '<eol>', '13'],
			['14', '15', '16', '<eol>'],
			['18', '19', '20', '21'],
			['22', '<eol>', '<eoc>', '23'],
			['<eol>', '<eoc>', '24', '25']
		])
