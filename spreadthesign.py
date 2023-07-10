import time
import unicodedata
import pandas as pd
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from urllib.parse import urljoin
import csv

categorias = 'https://www.spreadthesign.com/pt.br/search/by-category/'
urls_e_qtd_paginas = []

def obter_links_categorias(url):
    response = requests.get(url)
    html = response.text

    links = []

    soup = BeautifulSoup(html, 'html.parser')
    searchable_elements = soup.find_all(class_='js-searchable')

    for element in searchable_elements:
        anchor_tags = element.find_all('a')
        for tag in anchor_tags:
            if 'href' in tag.attrs:
                links.append('https://www.spreadthesign.com'+tag['href'])

    return links

def obter_qtd_paginas_categoria(url):
    qtd_paginas = 1

    while True:
        response = requests.get(url)
        html = response.text
        soup = BeautifulSoup(html, 'html.parser')

        link_prox_pagina = soup.find('div', class_='col-xs-4 search-pager-next').find('a')

        if link_prox_pagina: #se existir link pra prox
            qtd_paginas += 1
            url_prox_pagina = link_prox_pagina['href']
            url = urljoin(url, url_prox_pagina)
            # combina a URL base atual (url) com o caminho relativo da próxima página (url_prox_pagina)
        else:
            break # quando não existir mais

    return qtd_paginas

def gerar_vetor_urls_cada_categoria(urls_e_qtd_paginas):

    urls_categoria = []

    for url, num_paginas in urls_e_qtd_paginas:
        for pagina in range(1, num_paginas + 1):
            url_pagina = url + str(pagina)
            urls_categoria.append(url_pagina)

    return urls_categoria

def gerar_link_e_qtd_paginas(url):

    links = obter_links_categorias(url)

    for link in links:
        qtd_paginas = obter_qtd_paginas_categoria(link)
        print(link,qtd_paginas)
        urls_e_qtd_paginas.append((link, qtd_paginas))

    return urls_e_qtd_paginas

def obter_videos_site(categorias):
    urls_e_qtd_paginas = gerar_link_e_qtd_paginas(categorias)

    for url, num_paginas in urls_e_qtd_paginas:
        urls_cada_categoria = gerar_vetor_urls_cada_categoria([(url, num_paginas)])

        options = Options()
        #options.headless = True Ativado para que o navegador não seja aberto.

        driver = webdriver.Chrome(options=options)

        lista_videos = []

        for url in urls_cada_categoria:
            driver.get(url)
            time.sleep(5)  # delay para carregar a página

            html = driver.page_source  # pega o html
            soup = BeautifulSoup(html, 'html.parser')  # organiza

            # Encontrar todas as divs com a classe search-result-title (onde estão as palavras)
            divs = soup.find_all('div', class_='search-result-title')

            for div in divs:
                atags = div.find_all('a')  # atags = todos os "a"

                for a in atags:
                    # Excluir a tag <small> do conteúdo de cada "a", pois não queremos "Substantivo", "verbo", etc.
                    small_tag = a.find('small')
                    if small_tag:
                        small_tag.decompose()

                    # Extrair o texto do elemento 'a'
                    text = a.get_text(strip=True) 
                    # strip=True remove espaços em branco extras no início e no final do texto.

                    # Remover caracteres de controle e normalizar os caracteres Unidecode
                    text = "".join(ch for ch in text if unicodedata.category(ch)[0] != "C")
                    text = unicodedata.normalize('NFKD', text).encode('ascii', 'ignore').decode('utf-8')

                    # Obter o link do elemento 'a'
                    href = a['href']

                    # Abrir o link em uma nova aba
                    driver.execute_script("window.open(arguments[0], '_blank');", href)
                    time.sleep(1)  # Aguardar um segundo após o clique

                    # Alternar para a nova aba
                    driver.switch_to.window(driver.window_handles[-1])

                    # Obter o HTML da nova página
                    video_html = driver.page_source
                    video_soup = BeautifulSoup(video_html, 'html.parser')

                    # Encontrar a div que contém o vídeo
                    video_div = video_soup.find('div', class_='col-md-7')

                    if video_div:
                        # Verificar se há um elemento de vídeo presente
                        video_tag = video_div.find('video')
                        if video_tag:
                            # Obter o valor do atributo 'src' do vídeo
                            video_src = video_tag.get('src')
                            lista_videos.append((text, video_src))
                        else:
                            lista_videos.append((text, 'null'))
                    else:
                        lista_videos.append((text, 'null'))

                    # Fechar a nova aba e voltar para a aba anterior
                    driver.close()
                    driver.switch_to.window(driver.window_handles[0])

        driver.quit()
        print(lista_videos)
        df_videos = pd.DataFrame(lista_videos, columns=['Palavra', 'Link'])
        df_videos['Instituicao'] = 'Spread the Sign' 

    return df_videos

df_videos = obter_videos_site(categorias)
pd.set_option('display.max_columns', None)
pd.set_option('display.max_rows', None)
pd.set_option('display.width', None)
print(df_videos)

# Salvar DataFrame em um arquivo CSV
nome_arquivo = 'spreadthesign.csv'
formato = {
    'Palavra': str,
    'Link': str,
    'Instituicao': str
}
with open(nome_arquivo, 'w', newline='', encoding='utf-8') as arquivo_csv:
    escritor = csv.DictWriter(arquivo_csv, fieldnames=formato.keys())
    escritor.writeheader()
    for _, linha in df_videos.iterrows():
        escritor.writerow({campo: formato[campo](valor) for campo, valor in linha.items()})

print("Dados salvos em arquivo CSV:", nome_arquivo)

