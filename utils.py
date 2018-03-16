import tweepy, json, pymongo
import os
from twitterscraper import *

class StdOutListener(tweepy.StreamListener):

    def __init__(self):
        self.tweets = []
    def on_data(self, data):
        # Parsing
        decoded = json.loads(data)
        self.tweets.append(decoded)
        #print ("Writing tweets to file,CTRL+C to terminate the program")
        return True

    def on_error(self, status):
        print (status)

    def getTweets(self):
        return self.tweets



def getApiKeys(fileName = 'apiConfO'):
    with open (fileName, 'r') as file:
        apiConf = list(map(str.strip, file.read().split(",")))

    keys = {}
    keys['consumer key'] = apiConf[0]
    keys['consumer secret'] = apiConf[1]
    keys['access token key'] = apiConf[2]
    keys['access token secret'] = apiConf[3]

    return keys

def tweepyAutenticate(apiKeys):
    consumer_key = apiKeys['consumer key']
    consumer_secret = apiKeys['consumer secret']
    access_token_key = apiKeys['access token key']
    access_token_secret = apiKeys['access token secret']
    #creates the listener using my own access data to twitterAPI
    auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
    auth.set_access_token(access_token_key, access_token_secret)

    return auth


def recoverTweets(outputFile, authors=[], wordsSearched=[], startingDate='', endingDate=''):
    import subprocess
    numOfAuthors = len(authors)
    numOfWords = len(wordsSearched)
    callVars = ['./recoverTweets.sh',str(numOfWords),str(numOfAuthors)]
    callVars.extend([word for word in wordsSearched]+[author for author in authors])
    if startingDate!='':
        callVars.extend(['-sd',startingDate])
    if endingDate!='':
        callVars.extend(['-ed',endingDate])
    callVars.append(outputFile)
    print(callVars)
    print("Querying twitterAPI by using TwitterScraper")
    subprocess.call(callVars)

    with open('data/'+outputFile+'tmp') as json_data:
        tweets = json.load(json_data)

    save(tweets,outputFile,onFile=True,onDb=True)
    print("Query ended. Tweets files saved on your filesystem and on mongo.")
    os.remove('data/'+outputFile+'tmp')


def save(tweets, collectionName, featuresToSave='all', onFile=False, onDb=True, dbName = 'tweets'):
        #open a file to store the status objects
        if featuresToSave!='all':
            filteredTweets = [{feature: tweet[feature] for feature in featuresToSave } for tweet in tweets]
            tweets = filteredTweets

        if onFile:
            i = 2
            tmpName = collectionName
            while os.path.exists("data/" + tmpName + "/"):
                tmpName = collectionName + str(i)
                i+=1
            collectionName = tmpName
            os.makedirs("data/" + collectionName)

            i = 0
            for tweet in tweets:
                file = open("data/"+ collectionName + "/" + str(i) + ".json", 'a')
                #write json to file
                file.write(json.dumps(tweet))
                file.close()
                i+=1

        if onDb:
            client = pymongo.MongoClient()
            try:
                db = client[dbName]
            except:
                dbName = 'tweets'
                db = client[dbName]
            tweetCollection = db[collectionName]
            tweetCollection.insert_many(tweets)
        return collectionName

def loadTweets(collectionName, fromFile = False, fromDb = False, dbName = 'tweets'):
    def loadFromFile():
        tweets = []
        jsonFiles = [json for json in os.listdir("data/" + collectionName) if json.endswith('.json')]
        for file in jsonFiles:
            with open("data/" + collectionName + "/" + file) as tweet:
                tweets.append(json.load(tweet))
        return tweets
    def loadFromDb():
        #please remember to start mongod service

        tweets = []
        client = pymongo.MongoClient()

        try:
            db = client[dbName]
            tweetCollection = db[collectionName]
        except:
            db = client['tweets']
            tweetCollection = db[collectionName]

        for tweet in tweetCollection.find({}, {'_id': 0}):
            tweets.append(tweet)
        return tweets

    if fromDb:
        return loadFromDb()
    if fromFile:
        return loadFromFile()
    return
