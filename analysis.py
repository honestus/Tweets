import pandas as pd
from utils import saveTweets, loadTweets
import os

def syncCollections():
    db = client['tweets']
    mongoCollections = db.collection_names()
    fileSystemCollections= [x for x in os.listdir('data/') if os.path.isdir('data/' + x)]
    print("Checking all the files needed are currently in MongoDB...")
    for collection in [fileSystemCollections]:
        print("checking for collection: ", collection)
        if not loadTweets(collectionName=collection, fromDb=True, dbName=''):
            tweetsToSave = loadTweets(fromDb=False,collectionName=collection)
            saveTweets(collectionName=collection, onDb=True, onFile=False,tweets=tweetsToSave)
            print("Automatically saved the tweets collection %s on mongoDB, starting from json files" %collection)
    for collection in [mongoCollections]:
        print("checking for collection: ", collection)
        if not loadTweets(collectionName=collection, fromDb=False, dbName=''):
            tweetsToSave = loadTweets(fromDb=True,collectionName=collection)
            saveTweets(collectionName=collection, onDb=False, onFile=True,tweets=tweetsToSave)
            print("Automatically saved the tweets collection %s on file system, starting from mongo DB" %collection)
    print("Done. MongoDB and filesystem now contain all the Tweets.")

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
