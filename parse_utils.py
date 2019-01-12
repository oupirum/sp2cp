from fix_typos import fix_typos
import re

def comment_to_tokens(comment):
	tokens = []
	lines = comment.split('\n')
	for line in lines:
		line = line.strip()
		if line:
			line = line.lower()
			line = fix_typos(line)
			line_tokens = str_to_tokens(line)
			if line_tokens:
				tokens.extend(line_tokens)
				tokens.append('<eol>')
	if tokens and tokens[-1] != '<eoc>':
		tokens.append('<eoc>')
	return tokens

def str_to_tokens(s):
	tokens = []
	for token in s.split(' '):
		process_token(token, tokens)
	return tokens

def process_token(token, tokens):
	token = token.strip()
	if not token:
		return False

	token = token.strip()
	if not token:
		return False
	if not re.search('[a-zа-яё0-9\-_–:()^=>$/]', token):
		return False

	if re.match('>+.', token):
		tokens.append('>')
		return process_token(re.sub('^>+', '', token), tokens)

	if re.fullmatch('[a-fole0-9]{32,}', token):
		return False
	if re.fullmatch('[a-z0-9.\-]+@[a-z0-9.\-]+', token):
		tokens.append('ti.hui@i.pidor.com')
		return True
	if token.startswith('chrome://flags'):
		tokens.append(token)
		return True
	if re.fullmatch('(https?://)?[a-z0-9.\-]+\.(com|net|ru|onion|org)/?[a-zа-яё0-9:/\-.?=_#$%]+', token):
		tokens.append(token)
		return True

	if re.fullmatch('т\.[еодп]\.?', token):
		tokens.append(re.sub('\.?$', '.', token))
		return True
	if re.fullmatch('.*?[0-9]*т\.р\.?', token):
		if re.search('[0-9]', token):
			tokens.append('<n>т.р.')
		else:
			tokens.append('т.р.')
		return True
	if token == '9000':
		tokens.append(token)
		return True
	if re.fullmatch('[0-9][\-+.0-9]*', token):
		tokens.append('<n>')
		return True
	if re.match('[0-9][\-+.0-9]*[\-/$]*[a-zа-яё]+', token):
		tokens.append('<n>')
		sts = re.sub('^[\-+.0-9]*[0-9](-?)(\$?)(/?)', '\\1 \\2 \\3 ', token).split(' ')
		for st in sts:
			process_token(st, tokens)
		return True

	if token == '(нет)':
		tokens.append(token)
		return True

	if re.fullmatch('.*?:\)+', token):
		process_token(re.sub(':\)+$', '', token), tokens)
		tokens.append(':)')
		return True
	if re.fullmatch('.*?:\(+', token):
		process_token(re.sub(':\(+$', '', token), tokens)
		tokens.append(':(')
		return True
	if re.fullmatch('.*?:d+', token):
		process_token(re.sub(':d+$', '', token), tokens)
		tokens.append(':d')
		return True
	if re.fullmatch('.*?xd+', token):
		process_token(re.sub('xd+$', '', token), tokens)
		tokens.append('xd')
		return True
	if re.fullmatch('.*?:[3з]', token):
		process_token(re.sub(':[3з]+$', '', token), tokens)
		tokens.append(':3')
		return True
	if re.fullmatch('.*?\^_\^', token):
		process_token(re.sub('\^_\^+$', '', token), tokens)
		tokens.append('^_^')
		return True

	if re.fullmatch('[a-zа-яё]+', token):
		tokens.append(token)
		return True

	if re.fullmatch('.*?\)+0+[)0]*', token):
		process_token(re.sub('\)+0+[)0]*$', '', token), tokens)
		tokens.append('))0')
		return True
	if re.fullmatch('.*?\(+9+[(9]*', token):
		process_token(re.sub('\(+9+[(9]*$', '', token), tokens)
		tokens.append('((9')
		return True
	if re.fullmatch('.*?!*1+[!1]+', token):
		process_token(re.sub('!*1+[!1]+$', '', token), tokens)
		tokens.append('!!11')
		return True
	if re.fullmatch('.*?([a-zа-яё])1{3,}', token):
		process_token(re.sub('1{3,}$', '', token), tokens)
		tokens.append('111')
		return True
	if re.fullmatch('.*?((\?+)?(!+\?+)+)', token):
		process_token(re.sub('(\?+)?(!+\?+)+$', '', token), tokens)
		tokens.append('!?')
		return True

	if re.fullmatch('[a-zа-яё0-9]+', token):
		tokens.append(token)
		return True

	if re.search('-+>+', token):
		sts = re.split('-+>+', token)
		for i, st in enumerate(sts):
			process_token(st, tokens)
			if i < len(sts) - 1:
				tokens.append('->')
		return True

	token = re.sub('-{2,}', '–', token)

	for char in ['.', ',', '!', '?', '(', ')', '-', '_', '+']:
		if re.fullmatch('.*?' + re.escape(char) + '{2,}', token):
			process_token(re.sub(re.escape(char) + '{2,}$', '', token), tokens)
			tokens.append(char * 3)
			return True
	for char in ['.', ',', '!', '?', '(', ')', '-', '_', '+']:
		if re.fullmatch(re.escape(char) + '{2,}.*?', token):
			tokens.append(char * 3)
			return process_token(re.sub('^' + re.escape(char) + '{2,}', '', token), tokens)

	for char in ['.', ',', '!', '?', ':', ';', '-', '–', '*', '=', '~', '$']:
		if re.fullmatch('.*?' + re.escape(char), token):
			process_token(re.sub(re.escape(char) + '$', '', token), tokens)
			tokens.append(char)
			return True
	for char in ['.', ',', '!', '?', ':', ';', '-', '–', '*', '=', '~', '$']:
		if re.fullmatch(re.escape(char) + '.*', token):
			tokens.append(char)
			return process_token(re.sub('^' + re.escape(char), '', token), tokens)

	for char in ['.', ',', '!', '?', ':', ';', '+', '*', '=', '–']:
		if re.search(re.escape(char), token):
			sts = re.split(re.escape(char), token)
			for i, st in enumerate(sts):
				if process_token(st, tokens) and i < len(sts) - 1:
					tokens.append(char)
			return True

	if re.search('[a-zа-яё$]+/[a-zа-яё]+', token):
		sts = token.split('/')
		for i, st in enumerate(sts):
			if process_token(st, tokens) and i < len(sts) - 1:
				tokens.append('/')
		return True

	if re.fullmatch('[(\[\]][a-zа-яё0-9].*', token):
		return process_token(re.sub('^[(\[\]]', '', token), tokens)
	if re.fullmatch('.*?[a-zа-яё0-9][)\[\]]', token):
		return process_token(re.sub('[)\[\]]$', '', token), tokens)

	if re.search('[()]', token):
		for st in re.split('[()]', token):
			process_token(st, tokens)
		return True

	if re.search('[.,!?;]-', token):
		sts = re.sub('([a-zа-яё0-9])([.,!?;])-([a-zа-яё0-9])', '\\1 \\2 - \\3', token).split(' ')
		for st in sts:
			process_token(st, tokens)
		return True

	tokens.append(token)
	return True
