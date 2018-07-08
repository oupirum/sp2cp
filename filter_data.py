import re

def filter_data(comment):
	lines = comment.split('\n')

	line_filters = list(filter(
			lambda name: name.startswith('skip_line_'),
			[k for k, v in globals().items()]))

	for i in range(len(lines) - 1, -1, -1):
		line = lines[i] + ''
		line = line.strip(' ᅠᅠᅠ 	 ')
		line = cut_by_regex(line, '^((ре)?-?ролл)[.,] ')
		line = cut_by_regex(line, '^((re)?-?roll)[.,] ')
		line = cut_by_regex(line, '[.,] ((ре)?-?ролл)[.,]?$')
		line = cut_by_regex(line, '[.,] ((re)?-?roll)[.,]?$')
		line = cut_by_regex(line, '(: )?https?://[a-z0-9#?=%&@\-_.:/)!]+$')
		line = cut_by_regex(line, 'https?://[a-z0-9#?=%&@\-_.:/()\[\]!,]+$')
		line = cut_by_regex(line, 'https?://[a-z0-9#?=%&@\-_.:/()\[\]!,]+ ')

		line = line.strip()
		if line != lines[i]:
			lines.pop(i)
			lines.insert(i, line)

		for lf in line_filters:
			if globals()[lf](line.lower()):
				lines.pop(i)

		if len(line) == 0:
			lines.pop(i)

	return '\n'.join(lines)

def cut_by_regex(line, regex):
	if re.search(regex, line, flags=re.U|re.I):
		line = re.sub(regex, '', line, flags=re.U|re.I)
	return line


def skip_line_short(line):
	return len(line) > 0 and len(line) < 2

def skip_line_quote(line):
	return re.match(r'>\d\d\d', line) != None

def skip_line_url(line):
	return line.startswith('http://') or line.startswith('https://')

def skip_line_exclude(line):
	words_to_exclude = [
		'bump', 'bamp', 'бамп', 'бумп', 'бапм', 'побампа',
		'ролл', 'роллллллл', 'roll', 'rollllll', 'реролл', 'reroll', 'roлл',
		'rолл', 'ллор', 'llor', 'hjkk', 'кщдд', 'кручу-верчу', 'кручу', 'рiлл',
		'рольчик', 'ролол', 'r0ll', 'rell', 'рольнём', 'рольнем', 'рролл',
		'r o l l', 'р о л л', 'poll', 'ro11', 'ро11',
		'test', 'тест',
		'sage', 'сажа',
		'source', 'соус', 'совас'
	]

	if line in words_to_exclude:
		return True

	for word in words_to_exclude:
		contains = \
			re.fullmatch(
				r'[^a-zа-яё0-9]*' + word + '.*?',
				line, re.U) \
			or re.fullmatch(
				r'.*?' + word + r'[^a-zа-яё0-9]*',
				line, re.U)
		if contains and len(line) - len(word) <= 16:
			return True

	return False

def skip_line_nonmean(line):
	for word in [
		'сажа сажа сажа сажа',
		'sage sage sage sage',
		'[назад]',
		'тематика [au',
		'тематика [au',
		'главная настройка mobile',
		'доски каталог ст',
		'[ b / vg / po / n',
		'[ответить в тред]',
		'image.',
		'[жирный] [наклонный] [цитирование',
		'кликни/брось файл/',
		'покупка пасскода позволяет обходить капчу. ',
		'перекот ',
		'перекат треда ',
		'xdddddddddd',
		'11010000 10011011 11010000 10111110 11010000 10111011 100000 110',
		'голова, дай денег',
		'голова дай денег',
		'голова, дай же мне денег',
		'пирамида дай денег',
	]:
		if line.startswith(word):
			return True
	return False
