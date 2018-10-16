import os
import pandas as pd
import numpy as np
import requests
from bs4 import BeautifulSoup
import datetime


# from plotly.graph_objs import *
# import plotly
# from plotly.offline import download_plotlyjs, init_notebook_mode, plot, iplot

class ScrapeProperty:
    """ Class for all Google Location Services functions and properties"""

    REQ_HEADERS = {'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
                   'accept-encoding': 'gzip, deflate, br',
                   'accept-language': 'en-US,en;q=0.8',
                   'upgrade-insecure-requests': '1',
                   'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3163.100 Safari/537.36'
                   }

    column_titles = ['Price',
                     'Area',
                     'Price Per Area',
                     'Beds',
                     'Baths',
                     'Street',
                     'City',
                     'State',
                     'Broker',
                     'Month',
                     'Day',
                     'Year']


    def __init__(self, prev_data_path=None):
        self.card_list = []
        self.data_new = None
        self.data = None
        self.data_old = None
        if prev_data_path is not None:
            self.ReadPrevData(prev_data_path=prev_data_path)

    def ScrapeZillow(self, url=None, pages=1):

        for page in np.arange(1, pages + 1):

            ## Getting City Names from the Dictionary
            url = url + '/' + str(page) + '_p'

            ## Check Site
            with requests.Session() as zillow_session:
                html = zillow_session.get(url, headers=self.REQ_HEADERS)

            ## Scrape HTML Data
            soup = BeautifulSoup(html.content, 'lxml')
            self.soup_text = soup.get_text()

            ## Iterate through Sections of the HTML
            cards = soup.find_all('div', {'class': 'zsg-photo-card-caption'})
            self.card_list = self.card_list + cards

    def ReadSoup(self):

        for card_index, card in enumerate(self.card_list):

            try:

                location_dict = {}

                location_dict['Price'] = self.__GetPrice(card=card)
                location_dict['Street'], location_dict['City'], location_dict['State'] = self.__GetAddress(card=card)
                location_dict['Broker'] = self.__GetBroker(card=card)
                location_dict['Beds'], location_dict['Baths'], location_dict['Area'] = self.__GetInfo(card=card)
                location_dict['Year'], location_dict['Month'], location_dict['Day'] = self.__GetDate()
                location_dict['Price Per Area'] = location_dict['Price'] / location_dict['Area']

                self.AddData(location_dict)

            except:
                pass

    def AddData(self, location_dict={}):

        for key, value in location_dict.items():
            location_dict[key] = [value]
        new_data = pd.DataFrame.from_dict(location_dict)
        self.data_new = pd.concat([self.data_new, new_data]) if self.data_new is not None else new_data
        self.data_new = self.data_new[self.column_titles]

    def ReadPrevData(self, prev_data_path=None):

        self.data_old = pd.read_csv(prev_data_path, sep=',')
        self.data_old = self.data_old.drop(list(self.data_old)[0], axis=1)
        self.data_old = self.data_old[self.column_titles]

    def CombinePrevData(self):

        if self.data_new is not None and self.data_old is not None:
            self.data = pd.concat([self.data_old, self.data_new])
            print('Combined Old and New Data')
            self.data = self.data.drop_duplicates(subset=['Street', 'City', 'Month', 'Day', 'Year'])
        else:
            print('Data was not combined because either new or old data is empty')

    def SaveData(self, data_path=None):

        index = data_path.find('.csv')
        new_data_path = data_path[:index] + '_new' + data_path[index:]
        old_data_path = data_path[:index] + '_old' + data_path[index:]

        self.data_old.to_csv(old_data_path, sep=',')
        self.data.to_csv(data_path, sep=',')
        self.data_new.to_csv(new_data_path, sep=',')

    def __GetPrice(self, card=None):

        price = card.find('span', {'class': 'zsg-photo-card-price'}).text
        price = price.replace(',', '').replace('$', '')
        price = ''.join(ch for ch in price if ch.isdigit())
        price = float(price)
        return price

    def __GetAddress(self, card=None):

        address = card.find('span', {'class': 'zsg-photo-card-address'}).text
        address = address.split(',')
        street = address[0]
        city = address[1][1:]
        state = address[2].replace(' ', '')
        return street, city, state

    def __GetBroker(self, card=None):

        try: broker = card.find('span', {'class': 'zsg-photo-card-broker-name'}).text
        except: broker = 'NaN'
        return broker

    def __GetInfo(self, card=None):

        info = card.find('span', {'class': 'zsg-photo-card-info'}).text
        info = info.split()

        try: beds = float(info[0])
        except: beds = 0

        try: baths = float(info[3])
        except: baths = 0

        try:
            area = info[6].replace(',', '')
            area = ''.join(ch for ch in area if ch.isdigit())  # Remove Letters
            area = float(area)
        except:
            area = 0

        return beds, baths, area

    def __GetDate(self):

        now = datetime.datetime.now()
        return now.year, now.month, now.day

