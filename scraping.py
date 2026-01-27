import requests 
from bs4 import BeautifulSoup


pagina = requests.get("https://quotes.toscrape.com/")

dados_pagina = BeautifulSoup(pagina.content, 'html.parser')

# print(dados_pagina.prettify())

todas_frases = dados_pagina.find_all('span', itemprop="text")

for div in todas_frases:
    print(div.text)