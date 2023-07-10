import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from bs4 import BeautifulSoup
from selenium.webdriver.chrome.options import Options
import pandas as pd
import unidecode
import csv


options = Options()
driver = webdriver.Chrome(options=options)
driver.get('https://signbank.libras.ufsc.br/pt/search-signs/words?page=1&letter=a')



