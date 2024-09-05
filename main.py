import traceback, aiofiles, datetime, logging, asyncio, random, httpx, socks, json, time, re, os

from config import *

##############################################################################
logging.basicConfig(format=u'%(filename)s [LINE:%(lineno)d] #%(levelname)-8s [%(asctime)s]  %(message)s', level=logging.INFO)
logging.getLogger('httpx').setLevel(logging.WARNING)
##############################################################################

async def read_file(file_path: str, splitlines: bool = True):
	file_text = await (await aiofiles.open(file_path, 'r', encoding='utf-8')).read()
	return file_text.splitlines() if splitlines else file_text

class ProxyManager:
	def __init__(self, proxies: list = None, proxy_path: str = None):
		if proxies: self.proxies_to_check = proxies
		elif proxy_path and os.path.exists(proxy_path): self.proxies_to_check = open(proxy_path, 'r', encoding='utf-8').read().splitlines()
		else: self.proxies_to_check = []
		self.proxies = {}
		self.clients = {}

	def get_proxy(self, is_httpx: bool = True):
		try:
			min_usage_proxy = min(self.proxies, key=self.proxies.get)
			self.proxies[min_usage_proxy] += 1
			if is_httpx:
				_proxy = min_usage_proxy.split(':')
				proxy_formated = f'{"http" if proxy_protocol["http"] else "socks5"}://{_proxy[2]}:{_proxy[3]}@{_proxy[0]}:{_proxy[1]}'
				return {'http://': proxy_formated, 'https://': proxy_formated}
			else: return min_usage_proxy.split(':')
		except: return None

	def get_client(self, proxy):
		if isinstance(proxy, str) and proxy in self.clients: client = self.clients[proxy]
		elif isinstance(proxy, dict) and proxy.get('http://', None) in self.clients: client = self.clients[proxy.get('http://', None)]
		else:
			if isinstance(proxy, str):
				_proxy = proxy.split(':')
				proxy_formated = f'{"http" if proxy_protocol["http"] else "socks5"}://{_proxy[2]}:{_proxy[3]}@{_proxy[0]}:{_proxy[1]}'
				client = httpx.AsyncClient(proxies=proxy_formated)
			else: client = httpx.AsyncClient(proxies=proxy)
		return client

	def record_proxy_usage(self, proxy):
		if proxy in self.proxies:
			self.proxies[proxy] -= 1

	async def proxy_check_(self, proxy):
		_proxy = proxy.split(':')
		try:
			proxy_formated = f'{"http" if proxy_protocol["http"] else "socks5"}://{_proxy[2]}:{_proxy[3]}@{_proxy[0]}:{_proxy[1]}'
			async with httpx.AsyncClient(proxies={'http://': proxy_formated, 'https://': proxy_formated}) as client:
				await client.get('http://ip.bablosoft.com')
			self.proxies[proxy] = 0
		except:
			logging.info(f'[proxy_check] Невалидный прокси: {proxy}')
			if proxy in self.proxies: del self.proxies[proxy]

	async def proxy_check(self):
		logging.info(f'Проверяю {len(self.proxies_to_check)} прокси')
		futures = []
		for proxy in list(self.proxies_to_check):
			futures.append(self.proxy_check_(proxy))
		await asyncio.gather(*futures)
		logging.info(f'Валидных прокси: {len(self.proxies)} шт.')


class Parser:
	def __init__(self, proxy_client: ProxyManager, categories_to_parse: list = [], min_price: int = 0, max_price: int = 0, pages_to_parse: int = 0, check_seller_threads: bool = False, max_seller_threads_count: int = 0, skip_accounts_with_rating: bool = False, sort_by_date: bool = False, thread_creation_date: str = None, save_path: str = None, parsed_threads: list = []):
		self.proxy_client = proxy_client
		self.categories_to_parse = categories_to_parse
		self.min_price = min_price
		self.max_price = max_price
		self.pages_to_parse = pages_to_parse
		self.check_seller_threads = check_seller_threads
		self.max_seller_threads_count = max_seller_threads_count
		self.skip_accounts_with_rating = skip_accounts_with_rating
		self.sort_by_date = sort_by_date
		self.thread_creation_date = datetime.datetime.strptime(thread_creation_date, '%d.%m.%Y')
		self.save_path = save_path

		self.base_url = 'https://www.gumtree.com'
		self.headers = {'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7', 'accept-language': 'ru,en-US;q=0.9,en;q=0.8,ru-RU;q=0.7', 'priority': 'u=0, i', 'referer': 'https://www.gumtree.com/for-sale/computers-software', 'sec-ch-ua': '"Chromium";v="128", "Not;A=Brand";v="24", "Google Chrome";v="128"', 'sec-ch-ua-mobile': '?0', 'sec-ch-ua-platform': '"Windows"', 'sec-fetch-dest': 'document', 'sec-fetch-mode': 'navigate', 'sec-fetch-site': 'same-origin', 'sec-fetch-user': '?1', 'upgrade-insecure-requests': '1', 'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36'}
		self.parsed_threads = parsed_threads
		self.clients = {}

	def format_url(self, category: str, **kwargs):
		url = f'{self.base_url}/search'
		params = {'search_category': category, 'min_price': self.min_price, 'max_price': self.max_price}
		if self.sort_by_date: params['sort'] = 'date'
		params = {**params, **kwargs}
		return (url, params)

	async def save_to_file(self, text: str):
		async with aiofiles.open(save_path, 'a', encoding='utf-8') as out:
			await out.write(f'{text}\n')

	async def parse_category(self, category: str):
		url, params = self.format_url(category)
		while True:
			try:
				proxies = self.proxy_client.get_proxy()
				aclient = self.proxy_client.get_client(proxies)
				print(aclient)
				async with aclient as client:
					resp = await client.get(url, params=params, headers=self.headers)
					if resp.status_code == 200:
						break
					else:
						logging.info(f'[{"parse_category"}]: {resp.status_code} | {params.get("search_category", None)}')
						await asyncio.sleep(antiflood_sleep_time.get("parse_category", 5))
						proxies = self.proxy_client.get_proxy()
			except Exception as e: logging.error(f'Ошибка при запросе на {url}: {e}')

		tasks = []
		for page_idx in range(1, self.pages_to_parse+1):
			tasks.append(self.find_threads_per_page(proxies, category, page_idx))
		await asyncio.gather(*tasks)

	async def find_threads_per_page(self, proxies: str, category: str, page_idx: int):
		url, params = self.format_url(category, page=page_idx)
		while True:
			try:
				async with self.proxy_client.get_client(proxies) as client:
					resp = await client.get(url, params=params, headers=self.headers)
					if resp.status_code == 200:
						threads_on_page = resp.text.count('"position":')
						threads = json.loads(resp.text.split('application/ld+json">')[1].split('</script>')[0]).get('itemListElement', [])
						break
					else:
						logging.info(f'[{"find_threads_per_page"}]: {resp.status_code} | {params.get("search_category", None)}')
						await asyncio.sleep(antiflood_sleep_time.get("find_threads_per_page", 5))
						proxies = self.proxy_client.get_proxy()
			except Exception as e: logging.error(f'Ошибка при запросе на {url}: {e}')


		logging.info(f'[{category}|{page_idx}] Найдено объявлений: {len(threads)}')
		v = 0
		for thread in threads:
			thread_url = thread.get('url', '')
			if not thread_url.startswith('https://www.'): thread_url = thread_url.replace('https://', 'https://www.')
			if thread_url == '' or thread_url in self.parsed_threads: continue
			
			thread_title = thread.get('name', None)
			is_parsed = await self.parse_thread(thread_url, proxies=proxies, thread_title=thread_title)
			if is_parsed: v += 1
			self.parsed_threads.append(thread_url)
		logging.info(f'[{category}|{page_idx}] Спаршено объявлений: {v} из {len(threads)}')

	async def parse_thread(self, thread_url: str, proxies: str, thread_title: str = None):
		while True:
			try:
				async with self.proxy_client.get_client(proxies) as client:
					resp = await client.get(thread_url, headers=self.headers)
					if resp.status_code == 200:
						thread_html = resp.text
						break
					else:
						logging.info(f'[{"parse_thread"}]: {resp.status_code} | {params.get("search_category", None)}')
						await asyncio.sleep(antiflood_sleep_time.get("parse_thread", 5))
						proxies = self.proxy_client.get_proxy()
			except Exception as e: logging.error(f'Ошибка при запросе на {url}: {e}')

		thread_creation_date = datetime.datetime.strptime(thread_html.split('creationDate": "')[1].split('"')[0].split('T')[0], '%Y-%m-%d')
		if self.sort_by_date and not (thread_creation_date == self.thread_creation_date): return False

		try:
			if self.skip_accounts_with_rating:
				try:
					thread_rating = thread_html.split('<div class="seller-name-rating-bundle ')[1].split('"><s')[0].strip()
					if thread_rating == '':
						thread_rating = thread_html.split('<span class="count">(<!-- -->')[1].split('<!-- -->)</span>')[0].strip()
				except:
					thread_rating = thread_html.split('<span class="count">(<!-- -->')[1].split('<!-- -->)</span>')[0].strip()
				if thread_rating != 'no-rating': return False

			if not thread_title: thread_title = thread_html.split('<title>')[1].split(' |')[0]
			thread_price = thread_html.split('<h3 content="')[1].split('" data-q="ad-price"')[0]
			thread_currency = thread_html.split('"priceCurrency":"')[1].split('"')[0]
			if '<img src="https://imagedelivery.net/' in thread_html: thread_img = f'''https://imagedelivery.net/{thread_html.split('<img src="https://imagedelivery.net/')[1].split('"')[0]}'''
			else: thread_img = f'''https://www.google.com/maps/embed/{thread_html.split('src="https://www.google.com/maps/embed/')[1].split('"')[0]}'''

			if self.check_seller_threads:
				if '<a href="/profile/account/' not in thread_html: return False
				thread_profile = thread_html.split('<a href="/profile/account/')[1].split('"')[0]
				resp, proxies = await self.get(url=f'https://www.gumtree.com/profile/account/{thread_profile}')
				try: seller_threads_count = int(resp.text.split('<h2 class="css-v1sa9n e1l2cxkl9">')[1].split()[0])
				except: seller_threads_count = 0
				if seller_threads_count <= self.max_seller_threads_count:
					await self.save_to_file(f'{thread_url}|{thread_title}|{thread_price}|{thread_currency}|{thread_img}')
					return True
			else:
				await self.save_to_file(f'{thread_url}|{thread_title}|{thread_price}|{thread_currency}|{thread_img}')
				return True
		except Exception as e: ...


async def main():
	categories_to_parse = [(x.split('/')[-1] if x.startswith('http') else x) for x in await read_file(categories_to_parse_path)]
	parsed_threads = [x.split('|')[0] for x in await read_file(save_path)]
	proxy_client = ProxyManager(proxy_path=proxy_path)
	await proxy_client.proxy_check()
	parser_client = Parser(proxy_client=proxy_client, categories_to_parse=categories_to_parse, min_price=min_price, max_price=max_price, pages_to_parse=pages_to_parse, check_seller_threads=check_seller_threads, max_seller_threads_count=max_seller_threads_count, skip_accounts_with_rating=skip_accounts_with_rating, sort_by_date=sort_by_date, thread_creation_date=thread_creation_date, save_path=save_path, parsed_threads=parsed_threads)

	while True:
		tasks = []
		for category in categories_to_parse:
			tasks.append(parser_client.parse_category(category))
		await asyncio.gather(*tasks)
		logging.info('')

if __name__ == '__main__':
	asyncio.run(main())