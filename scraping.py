import requests 
from bs4 import BeautifulSoup


pagina = requests.get("https://quotes.toscrape.com/")

dados_pagina = BeautifulSoup(pagina.content, 'html.parser')

# print(dados_pagina.prettify())

# def filtro(classe_css):
#     return classe_css is not None and len(classe_css) == 4

todas_frases = dados_pagina.find_all('span', itemprop="text")

for div in todas_frases:
    print(div.text)