### PARSE SETTINGS
categories_to_parse_path = 'data/cats.txt' # Путь до файла с категориями для парсинга
min_price = 5					# Минимальная цена
max_price = 999					# Максимальная цена
pages_to_parse = 3				# Сколько страниц объявлений спарсить
check_seller_threads = False		# Проверять количество объявлений у продавца
max_seller_threads_count = 3	# Максимальное кол-во объявлений продавца
skip_accounts_with_rating = True	# Пропускать аккаунты с рейтингом

sort_by_date = False			# Сортировка по дате
thread_creation_date = '04.09.2024'	# Дата создания объявления. Формат: '31.12.2024'
save_path = 'data/result.txt'	# Путь до файла для сохранения

antiflood_sleep_time = { # Время для сна перед след. попыткой при срабатывании антифлуда
	'parse_category': 1,
	'find_threads_per_page': 1,
	'parse_thread': 1,
}

### PROXY
proxy_path = 'data/proxy.txt' # Путь до файла с прокси
proxy_protocol = { # Протокол прокси. Выбирать один
	'http': True,
	'socks5': False
}