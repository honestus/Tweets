import tweepy, json, pymongo
import os
from twitterscraper import *

global api, stream

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



def getApiKeys(fileName):
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

def startTwitterApi(keys):
    global api
    auth = tweepyAutenticate(keys)
    api = tweepy.API(auth)

"""def filterTweets(tweets, removeRetweets=True):
    ### replacing truncated tweet with extended ones
    for tweet in listener.getTweets():
    if 'extended_tweet' in tweet:
        tweet['text'] = tweet['extended_tweet']['full_text']
        del(tweet['extended_tweet']['full_text'])
        for k in list(tweet['extended_tweet'].keys()):
            tweet[k] = tweet['extended_tweet'][k]
    if 'extended_entities' in tweet:
        for k in tweet['extended_entities']:
            tweet['entities'][k]=tweet['extended_entities'][k]
    ### removing tweets referring to retweets
    if removeRetweets:
"""



def recoverTweets(outputCollection, authors=[], words=[], startingDate=None, endingDate=None, maxTweets=1000):
    if not isinstance(words, list):
        words = list([words])
    if not isinstance(authors, list):
        authors = list([authors])

    def getTweets():
        return

    def getTwitterscraperTweets():
        import subprocess
        numOfAuthors = len(authors)
        numOfWords = len(wordsSearched)
        callVars = ['./recoverTweets.sh',str(numOfWords),str(numOfAuthors)]
        callVars.extend([word for word in wordsSearched]+[author for author in authors])
        if startingDate!='':
            callVars.extend(['-sd',startingDate])
        if endingDate!='':
            callVars.extend(['-ed',endingDate])
        #if maxTweets:
        #    callVars.extend(['-max',str(maxTweets)])
        callVars.append("data/"+outputCollection+"tmp")
        print("Querying twitterAPI by using TwitterScraper... (it may take a long time)")
        subprocess.call(callVars)
        with open('data/'+outputCollection+'tmp') as json_data:
            tweets = json.load(json_data)
        print("Query ended. Retrieved: ",len(tweets)," tweets")
        #saveTweets(tweets,outputCollection,onFile=True,onDb=True)
        os.remove('data/'+outputCollection+'tmp')
        return tweets

    if startingDate is None  & endingDate is None:
        return getTweets()
    return getTwitterscraperTweets()

# Register an handler for the timeout
def __streamHandler__(signum, frame):
    raise Exception("end of time")

# This function *may* run for an indetermined time...
def __stream__(stream, words):
    stream.filter(track=words)

def streamTweets(words, timeLimit=120):
    if not 'stream' in globals():
        global stream
        listener = StdOutListener()
        auth = api.auth
        stream = tweepy.Stream(auth, listener)
    if not isinstance(words, list):
        words = list([words])
    import signal
    # Register the signal function handler
    signal.signal(signal.SIGALRM, __streamHandler__)
    # Define a timeout for your function
    signal.alarm(timeLimit)
    try:
       __stream__(stream,words)
    except Exception:
        print("Streaming over after time period of", timeLimit, "seconds... Retrieved", len(stream.listener.getTweets()), "tweets.")
        stream.disconnect()
    return stream.listener.getTweets()

def getTweetById(tweetId):
    api = getTwitterApi()
    return api.get_status(tweetId)


def saveTweets(tweets, collectionName, featuresToSave='all', onFile=False, onDb=True, dbName = 'tweets'):
        #open a file to store the status objects
        if featuresToSave!='all':
            filteredTweets = [{feature: tweet[feature] for feature in featuresToSave } for tweet in tweets]
            tweets = filteredTweets

        if onFile:
            print("Saving Tweets on filesystem...")
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
            print("Done. Tweets correctly saved on your filesystem.")

        if onDb:
            print("Saving Tweets on MongoDB...")
            client = pymongo.MongoClient()
            try:
                db = client[dbName]
            except:
                dbName = 'tweets'
                db = client[dbName]
            tweetCollection = db[collectionName]
            tweetCollection.insert_many(tweets)
            print("Done. Tweets correctly saved on MongoDB")
        return collectionName

def loadTweets(collectionName, fromDb = False, dbName = 'tweets'):
    def loadFromFile():
        print ("Loading tweets from file...")
        tweets = []
        try:
            jsonFiles = [json for json in os.listdir("data/" + collectionName) if json.endswith('.json')]
        except:
            print("Cannot load tweets from specified path. No directory called: " + collectionName)
            return
        for file in jsonFiles:
            with open("data/" + collectionName + "/" + file) as tweet:
                tweets.append(json.load(tweet))
        print("Done. Tweets correctly loaded")
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
        if (not collectionName in db.collection_names()):
            print("Cannot load tweets from db. No collections called: " + collectionName)
            return None
        for tweet in tweetCollection.find({}, {'_id': 0}):
            tweets.append(tweet)
        print("Done. Tweets correctly loaded")
        return tweets

    if fromDb:
        return loadFromDb()
    return loadFromFile()
