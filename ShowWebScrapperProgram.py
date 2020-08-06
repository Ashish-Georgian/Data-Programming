#!/usr/bin/env python
# coding: utf-8

from urllib.request import Request, urlopen
from bs4 import BeautifulSoup
import requests
import pandas as pd
import numpy as np
import pymysql
from sqlalchemy import create_engine
from sqlalchemy.sql import text
from apscheduler.schedulers.blocking import BlockingScheduler
scheduler = BlockingScheduler()

# Header while making web request
HEADERS = ({'User-Agent':
            'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2228.0 Safari/537.36',
            'Accept-Language': 'en-US, en;q=0.5'})

			
# Function to get the URL of next button on the webpage
def last_url(i):
    u = -1
    try:
        u = 'https://www.amazon.com' + s.find("li",attrs={"class":"a-last"}).find("a").get('href')
    except:
        return u
    return u


# Function to get product name
def get_title(i):
    n = -1
    try:
        n = i.find("div",attrs={"class":"a-section a-spacing-none a-spacing-top-small"}).find("h2",attrs={"class":"a-size-mini a-spacing-none a-color-base s-line-clamp-4"}).find("a",attrs={"class":"a-link-normal a-text-normal"}).find("span",attrs={"class":"a-size-base-plus a-color-base a-text-normal"}).text
    except:
        return n
    return n


# Function to get MRP Price and selling price
def get_price_and_mrp(i):
    n = -1
    q = -1
    temp = 0
    l = []
    try:
        for j in i.find("div",attrs={"class":"a-row a-size-base a-color-base"}).find("div",attrs={"class":"a-row"}).findAll("span",attrs={"class":"a-offscreen"}):
            if temp == 0:
                n = j.text
                temp = temp+1
            else:
                q = j.text
    except:
        pass
    return n,q


# Function to get Rating of the product
def get_rating(i):
    n = -1
    try:
        n = i.find("div",attrs={"class":"a-section a-spacing-none a-spacing-top-micro"}).find("div",attrs={"class":"a-row a-size-small"}).find("a",attrs={"class":"a-popover-trigger a-declarative"}).find("span",attrs={"class":"a-icon-alt"}).text
    except:
        return n
    return n


# Function to get URL of the product
def get_url(i):
    n = -1
    try:
        n = 'https://www.amazon.com' + i.find("span",attrs={"class":"rush-component"}).find("a",attrs={"class":"a-link-normal s-no-outline"}).get('href')
    except:
        return n
    return n



# Function to get Number of the reviewer on the product
def get_reviewers(i):
    n = -1
    try:
        n = i.find("div",attrs={"class":"a-section a-spacing-none a-spacing-top-micro"}).find("div",attrs={"class":"a-row a-size-small"}).find("a",attrs={"class":"a-link-normal"}).find("span",attrs={"class":"a-size-base"}).text
    except:
        return n
    return n



# Function to get category of the product
def category_of_shoe(x):
    texts = x.split(" ")
    i = 0
    category = ''
    for j in texts:
        if (('SHOE' == str(j).upper()) | ('SHOWS' == str(j).upper())):
            if i!=0:
                category = str(texts[i-1]).upper()+' SHOE'
                break
        i = i+1
    return category



# Function to write the data into database
def cleanedDataToMySQL(cleaned):
    try:
        session = create_engine('mysql+pymysql://b1988b353f38a9:eb355ccd@us-cdbr-east-02.cleardb.com:3306/heroku_57e05bf7b956609')
        #cleaned_dataset.to_sql(name='amazon_shoe_store',con=session, if_exists='append', index=False)
        print('Number of Record inserted into the database: '+str(cleaned.shape[0]))
    except:
        print('Issue while Accessing the heroku server')



# Function to Clean the data
def dataCleaning(products,prices,ratings,number_of_customers,mrp_prices,urls):
    cleaned = pd.DataFrame({'product':products,'price':prices,'mrp_price':mrp_prices,'rating':ratings,'number of rater':number_of_customers,'product_url':urls})
    cleaned = cleaned.drop_duplicates(keep='first').reset_index(drop='index')
    cleaned = cleaned[['product','mrp_price','price','rating','number of rater','product_url']]
    cleaned.rename(columns={'number of rater':'reviews'},inplace=True)
    cleaned.replace(-1,np.nan,inplace=True)
    cleaned.mrp_price.fillna(cleaned.price,inplace=True)
    cleaned.rename(columns={'price':'sell_price'},inplace=True)
    cleaned['rating'] = cleaned['rating'].astype(str)
    cleaned['rating'] = cleaned.rating.apply(lambda x: x.split(' ')[0])
    cleaned['product'] = cleaned['product'].astype(str)
    cleaned['category'] = cleaned['product'].apply(lambda x: category_of_shoe(x))
    cleaned['mrp_price'] = cleaned['mrp_price'].str.replace(',', '')
    cleaned['mrp_price'] = cleaned['mrp_price'].str.replace('$', '')
    cleaned['mrp_price'] = cleaned['mrp_price'].astype(float)
    cleaned['sell_price'] = cleaned['sell_price'].str.replace(',', '')
    cleaned['sell_price'] = cleaned['sell_price'].str.replace('$', '')
    cleaned['sell_price'] = cleaned['sell_price'].astype(float)
    cleaned['reviews'] = cleaned['reviews'].str.replace(',', '')
    cleaned['reviews'] = cleaned['reviews'].astype(float)
    cleaned['rating'] = cleaned['rating'].astype(float)
    number_of_records = cleaned.shape[0]
    if number_of_records > 14000:
        cleaned = cleaned.sample(n=14000).reset_index(drop='index')
        cleaned_dataset.to_csv('Amazon_shoe_store14k.csv',index=False)
    cleanedDataToMySQL(cleaned)



# Function to acquire the data
@scheduler.scheduled_job('interval', seconds=86400)
def data_acquisition():
    # Variable which consist the URL(s) from where data needs to scrapped
    # Read from configuration file
    print('Data Acquisition is started')
    master_urls = pd.read_csv('master_url_configuration.csv')
    master_urls = list(master_urls['master_url'])
    # Variable initialisation
    products = []
    prices = []
    ratings = []
    number_of_customers= [] 
    mrp_prices = []
    urls = []
    visited_pages = 0
    for tt in master_urls:
        base_url = tt
        while base_url!= -1:
            resp = requests.get(base_url,headers=HEADERS)
            s = BeautifulSoup(resp.content,features='lxml')
            for i in s.findAll("div",attrs={"class":"a-section a-spacing-medium"}):
                n = get_title(i)
                r = get_rating(i)
                n_r = get_reviewers(i)
                p,mrp_p = get_price_and_mrp(i)
                url = get_url(i)
                products.append(n)
                prices.append(p)
                mrp_prices.append(mrp_p)
                ratings.append(r)
                number_of_customers.append(n_r)
                urls.append(url)
            base_url = last_url(s)
            print(base_url)
            visited_pages = visited_pages + 1
    print('Number of web pages visited by program: '+str(visited_pages))
    dataCleaning(products,prices,ratings,number_of_customers,mrp_prices,urls)


if __name__ == '__main__':
    # Start the program
    data_acquisition()
    scheduler.start()
	