import os
import re

def main():
	files = os.listdir('./dataset/')
	for file in files:
		if not re.match('\d+\.txt', file):
			continue

		with open('./dataset/' + file, 'rb') as f:
			lines_src = f.read().decode('utf-8').split('\n')
			lines = process_lines(list(lines_src), file)

		if len(list(filter(lambda line: len(line) > 0, lines))) == 0 \
				or len('\n'.join(lines)) < 10:
			os.remove('./dataset/' + file)
			continue

		# print(file)
		# print('\n'.join([line.lower() for line in lines]) + '\n\n')

		if lines != lines_src:
			with open('./dataset/' + file, 'wb') as f:
				f.write('\n'.join(lines).encode('utf-8'))

def process_lines(lines, file):
	line_filters = list(filter(
			lambda name: name.startswith('skip_line'),
			[k for k, v in globals().items()]))
	num_empty = 0

	for i in range(len(lines) - 2, -1, -1):
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
				print('skip:', line)
				lines.pop(i)

		# if 'хах' in line:
		# 	print('warn:', line)

		# Find wipe
		if re.match('аноним [0-9]{2}/[0-9]{2}', line.lower()):
			print(file)
			print(line)

		if len(line) == 0:
			num_empty += 1
			if num_empty >= 2:
				lines.pop(i)
				num_empty -= 1
		else:
			num_empty = 0

	return lines

def cut_by_regex(line, regex):
	if re.search(regex, line, flags=re.U|re.I):
		line = re.sub(regex, '', line, flags=re.U|re.I)
		print('cut:', line)
	return line


def skip_line_short(line):
	return len(line) > 0 and len(line) < 3

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

		# if word in line:
		# 	print('warn:', line)

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
		'уебывай в /soc/',
		'голова, дай денег',
		'голова дай денег',
		'голова, дай же мне денег',
		'пирамида дай денег',
		'пиздуй в /sex/',
	]:
		if line.startswith(word):
			return True
	return False

def skip_line_ahah_regex(line):
	return re.fullmatch(r'[ахп)(!.]+', line, re.U) != None


if __name__ == '__main__':
	main()
