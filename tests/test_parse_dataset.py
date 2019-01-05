from parse_dataset import \
		parse_dataset, \
		comment_to_tokens
from parse_utils import process_token
import random

class TestParseDataset():

	def test_process_token(self):
		self.pt('qwe@gmail.com', ['ti.hui@i.pidor.com'])
		self.pt('10т.р', ['<n>т.р.'])
		self.pt('т.р.', ['т.р.'])
		self.pt('т.д', ['т.д.'])
		self.pt('100к', ['<n>', 'к'])
		self.pt('6666666666666666', ['<n>'])
		self.pt('3.5', ['<n>'])
		self.pt('2-ая', ['<n>', '-', 'ая'])
		self.pt('$10', ['$', '<n>'])
		self.pt('10/10', ['10/10'])
		self.pt('qwe/10', ['qwe/10'])
		self.pt('10/день', ['<n>', '/', 'день'])
		self.pt('10$/день', ['<n>', '$', '/', 'день'])
		self.pt('qwe/10', ['qwe/10'])
		self.pt('qwe/qwe', ['qwe', '/', 'qwe'])
		self.pt('------', ['–'])
		self.pt('------>', ['->'])
		self.pt('.....qwe', ['...', 'qwe'])
		self.pt('qwe:))', ['qwe', ':)'])
		self.pt('qwe:ddd', ['qwe', ':d'])
		self.pt('qwe)xd', ['qwe', 'xd'])
		self.pt('qwe:3', ['qwe', ':3'])
		self.pt('qwe))))00', ['qwe', '))0'])
		self.pt('qwe!!!11!!1!1!', ['qwe', '!!11'])
		self.pt('qwe1!!', ['qwe', '!!11'])
		self.pt('qwe111111', ['qwe', '!!11'])
		self.pt('qwe->', ['qwe', '->'])
		self.pt('qwe->123', ['qwe', '->', '<n>'])
		self.pt('qwe----->123', ['qwe', '->', '<n>'])
		self.pt('qwe!!!!!!!!!!!', ['qwe', '!!!'])
		self.pt('qwe!?', ['qwe', '!?'])
		self.pt('-qwe', ['-', 'qwe'])
		self.pt('qwe.rty', ['qwe', '.', 'rty'])
		self.pt('(qwe)', ['qwe'])
		self.pt('one(two),three', ['one', 'two', ',', 'three'])
		self.pt('one+two+three', ['one', '+', 'two', '+', 'three'])
		self.pt('qwe?-rty', ['qwe', '?', '-', 'rty'])
		self.pt('>>>qwe', ['>', 'qwe'])
		self.pt('>>>/qwe', ['>', '/qwe'])

	def pt(self, token, expect_tokens):
		tokens = []
		process_token(token, tokens)
		assert(tokens == expect_tokens)


	def test_parse_dataset(self):
		ds_dir = './tests/dataset/threads/'
		seqs, id2token, lexicon = parse_dataset(ds_dir, 3000, 6, 100)

		assert(len(seqs) > 200)
		assert(len(seqs) < 300)
		assert(len(seqs[0]) > 0)
		assert(len(seqs[-1]) > 0)

		assert(len(id2token) > 2000)
		assert(len(id2token) < 3000)

		assert('<pad>' not in lexicon)
		assert('<unk>' not in lexicon)
		assert('<eol>' in lexicon)
		assert('<eoc>' in lexicon)
		assert(len(id2token) == len(lexicon) + 2)  # words + <pad>, <unk>

		assert(lexicon[')))'] == 19)
		assert(lexicon['сельдь'] == 4)
		assert(lexicon['!?'] == 4)

		for i in range(0, 3):
			assert(random.choice(seqs).count(2) >= 2)  # <eol>
			assert(random.choice(seqs).count(3) == 2)  # <eoc>

	def test_comment_to_tokens(self):
		assert(comment_to_tokens('имея внешку 3 из 10. что тебе мешает завести хотя бы одну?') == ['имея', 'внешку', '<n>', 'из', '<n>', 'что', 'тебе', 'мешает', 'завести', 'хотя', 'бы', 'одну', '?', '<eol>', '<eoc>'])
		assert(comment_to_tokens('qwe<br> adasd') == ['qwe', 'adasd', '<eol>', '<eoc>'])
