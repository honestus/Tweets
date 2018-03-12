import pandas as pd
from utils import save, loadTweets
import os

def init():
    for collection in [x for x in os.listdir('data/') if os.path.isdir('data/' + x)]:
        if not loadTweets(collectionName=collection, fromDb=True, dbName=''):
            print("Automatically saved the tweets collection %s on mongoDB" %collection)
            tweetsToSave = loadTweets(fromFile=True,fromDb=False,collectionName=collection)
            save(collectionName=collection, onDb=True, onFile=False,tweets=tweetsToSave)

def mapSources(source):
    if 'android' in source.lower():
        return 'Android'
    elif any(x in source.lower() for x in ['iphone','ipad','mac','ios']):
        return 'IOS'
    elif 'windows' in source.lower():
        return 'Windows'
    elif 'web' in source.lower():
        return 'Web browsers'
    return 'Other'

def getNofNull(df,attributeName):
    return pd.isnull(df[attributeName]).sum()

def getPercentNull(df,attributeName):
    return getNofNull(df,attributeName)/len(df)

def getPercentValues(df,attributeName):
    return df.groupby(attributeName).size().apply(lambda x: float(x) / df.groupby(attributeName).size().sum()*100).sort_values(ascending=False)

init()
