import tweepy, json, pymongo
import os
from twitterscraper import *
from utils2 import splitIntegerIntoIntegers
from TextAnalysis import containsWord
import random

global api, stream

class StdOutListener(tweepy.StreamListener):
    """ MyListener class for tweepy StreamListener """
    def __init__(self, removeRetweets=False):
        self.tweets = []
        """ removeRetweets is a boolean to remove Retweets when streaming or not """
        self.removeRetweets = removeRetweets
    def on_data(self, data):
        # Parsing
        decoded = json.loads(data)
        try:
            if not self.removeRetweets or not isRetweet(decoded):
            ### appending tweet only if it's not retweeted(if requested)
                self.tweets.append(decoded)
        except:
            pass
        return True

    def on_error(self, status):
        print (status)

    def on_exception(self, exception):
        print (exception)

    def getTweets(self):
        return self.tweets

    def setRemoveRetweets(self, removeRetweets):
        self.removeRetweets = removeRetweets

    def getRemoveRetweets(self):
        return self.removeRetweets

    def resetTweets(self):
        self.tweets = []


def getApiKeys(fileName):
    """loads apiKeys from file. File must contain four strings(one per line), representing:
    consumer key, consumer secret, access token key, access token secret. """
    with open (fileName, 'r') as file:
        apiConf = list(map(str.strip, file.read().split(",")))

    keys = {}
    keys['consumer key'] = apiConf[0]
    keys['consumer secret'] = apiConf[1]
    keys['access token key'] = apiConf[2]
    keys['access token secret'] = apiConf[3]

    return keys

def tweepyAutenticate(apiKeys):
    """ apiKeys is a dictionary having 4 elements: consumer key, consumer secret, access token key, access token secret.
    Starting from this dict, the method validates an OAuthAndler from tweepy """
    consumer_key = apiKeys['consumer key']
    consumer_secret = apiKeys['consumer secret']
    access_token_key = apiKeys['access token key']
    access_token_secret = apiKeys['access token secret']
    #creates the listener using my own access data to twitterAPI
    auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
    auth.set_access_token(access_token_key, access_token_secret)

    return auth

def startTwitterApi(apiKeys):
    """ apiKeys is a dictionary having 4 elements: consumer key, consumer secret, access token key, access token secret.
    Starting from apiKeys, it makes an instance of tweepy.API. """
    global api
    auth = tweepyAutenticate(apiKeys)
    api = tweepy.API(auth)
    return api

"""def filterTweets(tweets, removeRetweets=True):
    ### replacing truncated tweet with extended ones
    for tweet in tweets:
        if 'extended_tweet' in tweet:
            tweet['text'] = tweet['extended_tweet']['full_text']
            del(tweet['extended_tweet']['full_text'])
            for k in list(tweet['extended_tweet'].keys()):
                tweet[k] = tweet['extended_tweet'][k]
        if 'extended_entities' in tweet:
            for k in tweet['extended_entities']:
                tweet['entities'][k]=tweet['extended_entities'][k]
        del(tweet['display_text_range'])
    ### removing tweets referring to retweets

    if removeRetweets:
"""


def getTweetById(tweetId):
    """ returns an (json) object representing the tweet retrieved for the specified id """
    if 'api' not in globals():
        startTwitterApi(getApiKeys(fileName="apiConf2.txt"))
    tmpTweet = api.get_status(tweetId, tweet_mode="extended")
    tmpTweet._json['text']=tmpTweet._json['full_text']
    del (tmpTweet._json['full_text'])
    return tmpTweet._json


def recoverTweets(authors=[], words=[], removeRetweets=False, sortBy='newest',**kwargs):
    """ returns a list of (json) objects representing the tweets retrieved containing the words specified(if any) and written
    by the chosen authors(if any). If removeRetweets, only the tweets that don't refere to a retweet will be retrieved.
    sortBy is the way to sort the retrievedTweets. It's very important if maxTweets is specified.
    ### :allowed_param: 'startingDate', 'endingDate', 'maxTweets', 'lang'
    ### allowed values for sortBy: 'newest', 'oldest', 'random', 'favorite_count', 'retweet_count' """
    authors = mapToValid(authors)
    words = mapToValid(words)

    def getTopNTweets(retrievedTweets, numberOfTweets):
        """Sort the retrievedTweets by sortBy specified and returns the top-N Tweets"""
        if sortBy=='newest':
            retrievedTweets = sorted(retrievedTweets, key=lambda k: k['id'], reverse=True)
        elif sortBy=='oldest':
            retrievedTweets = sorted(retrievedTweets, key=lambda k: k['id'],reverse=False)
        elif sortBy=='favorite_count':
            retrievedTweets = sorted(retrievedTweets, key=lambda k: k['favorite_count'],reverse=True)
        elif sortBy=='retweet_count':
            retrievedTweets = sorted(retrievedTweets, key=lambda k: k['retweet_count'],reverse=True)
        else:
            retrievedTweets = random.sample(retrievedTweets, numberOfTweets)
        return retrievedTweets[:numberOfTweets]

    def getTweetsByUser(username, maxTweets=1000):
        """Returns a list of (json) objects representing the tweets for a specified Twitter username.
        If any words is queried, it will filter out every tweet that doesn't contain any of those words."""
        if 'api' not in globals():
            startTwitterApi(getApiKeys(fileName="apiConf2.txt"))
        myTweets=[]
        if words:
            apiRes = tweepy.Cursor(api.user_timeline,screen_name=username, count=100, tweet_mode='extended', include_rts=not removeRetweets).items()
            for tweet in apiRes:
                if any(containsWord(tweet._json['full_text'],word) for word in words):
                    tweet._json['text']=tweet._json['full_text']
                    del (tweet._json['full_text'])
                    myTweets.append(tweet._json)
        else:
            if sortBy=='newest':
                for tweet in tweepy.Cursor(api.user_timeline,screen_name=username, count=100, tweet_mode='extended', include_rts=not removeRetweets).items(maxTweets):
                    tweet._json['text']=tweet._json['full_text']
                    del (tweet._json['full_text'])
                    myTweets.append(tweet._json)
            else:
                for tweet in tweepy.Cursor(api.user_timeline,screen_name=username, count=100, tweet_mode='extended', include_rts=not removeRetweets).items():
                    tweet._json['text']=tweet._json['full_text']
                    del (tweet._json['full_text'])
                    myTweets.append(tweet._json)

        return getTopNTweets(myTweets, maxTweets)

    def searchTweets():
        """ returns a list of (json) objects representing the tweets retrieved for a specified query.
        It doesn't work if any authors is specified.
        Then, startingDate and endingDate cannot be older than one week ago because of Twitter restrictions for standardAPI
        :reference: https://developer.twitter.com/en/docs/tweets/search/api-reference/get-search-tweets
        """
        if 'api' not in globals():
            startTwitterApi(getApiKeys(fileName='apiConf2.txt'))
        #SEARCHING TWEETS CONTAINING THE HASHTAG "#bitcoin" USING TWEEPY LIBRARY
        myTweets= []
        #words=list(map(str,words))
        if words:
            myQuery=' OR '.join(words)
        else:
            myQuery = '*'
        if removeRetweets:
            myQuery += ' - filter:retweets'
        kwargs['q']=myQuery
        kwargs['count']=100
        kwargs['tweet_mode']='extended'
        if 'startingDate' in kwargs:
            kwargs['since']=kwargs['startingDate']
            del(kwargs['startingDate'])
        if 'endingDate' in kwargs:
            kwargs['until']=kwargs['endingDate']
            del(kwargs['endingDate'])
        if 'maxTweets' in kwargs:
            del(kwargs['maxTweets'])
        if sortBy=='newest':
            for tweet in tweepy.Cursor(api.search, kwargs).items(maxTweets):
                tweet._json['text']=tweet._json['full_text']
                del (tweet._json['full_text'])
                myTweets.append(tweet._json)
        else:
            for tweet in tweepy.Cursor(api.search, kwargs).items():
                tweet._json['text']=tweet._json['full_text']
                del (tweet._json['full_text'])
                myTweets.append(tweet._json)
        return getTopNTweets(myTweets, maxTweets)


    def getTwitterscraperTweets():
        """ returns a list of (json) objects representing the tweets retrieved for the specified inputs.
        It's very useful to avoid restrictions such as number of requests or dates not older than 7 days ago for twitterAPI (and tweepy).
        It will call the recoverTweets.sh script to properly query the API by twitterscraper.
        :reference: https://github.com/taspinar/twitterscraper
        """
        import subprocess
        numOfAuthors = len(authors)
        numOfWords = len(words)
        callVars = ['./recoverTweets.sh',str(numOfWords),str(numOfAuthors)]
        callVars.extend([word for word in words]+[author for author in authors])
        if startingDate:
            callVars.extend(['-sd',startingDate])
        if endingDate:
            callVars.extend(['-ed',endingDate])
        #if maxTweets:
        #    callVars.extend(['-max',str(maxTweets)])
        callVars.append("data/twitterscrapertmp")
        print("Querying twitterAPI by using TwitterScraper... (it may take a long time)")
        subprocess.call(callVars)
        with open('data/twitterscrapertmp') as json_data:
            tweets = json.load(json_data)
        if removeRetweets:
            tweets = [tweet for tweet in tweets if not isRetweet(tweet)]
        print("Query ended. Retrieved: ",len(tweets)," tweets")
        #saveTweets(tweets,outputCollection,onFile=True,onDb=True)
        os.remove('data/twitterscrapertmp')
        return tweets


    if "maxTweets" in kwargs:
        maxTweets=kwargs['maxTweets']
    else:
        maxTweets=1000

    if len(authors)==0 and len(words)==0:
        return("qua") ###call sample function with maxTweets and (if any) dates
    if 'startingDate' in kwargs or 'endingDate' in kwargs:
        return getTwitterscraperTweets()

    if len(authors)!=0:
        tweets, splits, i = [], splitIntegerIntoIntegers(maxTweets,len(authors)), 0
        for author in authors:
            tweets.extend(getTweetsByUser(username=author, maxTweets=splits[i]))
            i+=1
        return tweets
    return getTweets()


# Register an handler for the timeout
def __streamHandler__(signum, frame):
    """handler function for stream timeout"""
    raise Exception("end of time")

# This function *may* run for an indetermined time...
def __stream__(myStream, **kwargs):
    """ stream function. It will call the filter function from tweepy Streaming
    :allowed_param: follow, track, locations, languages
    :reference: http://docs.tweepy.org/en/v3.4.0/streaming_how_to.html"""
    print(kwargs)
    d = kwargs
    myStream.filter(**d)

def streamTweets(words = [], authors = [], timeLimit=120, removeRetweets=False, **kwargs):
    """ Returns a list of (json) objects representing the tweets found in real time matching the specified inputs.
    :param: timeLimit is an integer that states the time (in seconds) of the streaming.
    It calls the __stream__ function with the specified input parameters.
    :allowed_param: locations, languages
    """
    if 'stream' not in globals():
        global stream
        if 'api' not in globals():
            startTwitterApi(getApiKeys(fileName="apiConf2.txt"))
        listener = StdOutListener(removeRetweets=removeRetweets)
        auth = api.auth
        stream = tweepy.Stream(auth, listener, tweet_mode='extended')
    else:
        stream.listener.setRemoveRetweets(removeRetweets)
        stream.listener.resetTweets()

    words = mapToValid(words)
    authors = mapToValid(authors)
    if not words and not authors:
        words=["the", "i", "to", "a", "and", "'s", "is", "in", "it", "you", "of", "for", "on", "my", "that", "e", "with", "me", "do", "have", "ciao", "o", "u", "cool", "good", "nice", "#", "*", ":", ";", ",", ".", "?", "-", "%", "$", "€", "!", "(", ")", "=", "'"]

        #myQuery = ' OR '.join(kwargs["words"])
    if authors:
        kwargs["follow"]=[user.id_str for user in list(map(api.get_user,authors))]
    else:
        kwargs["track"]=words
    #if removeRetweets:
    #    myQuery += " -filter:retweets"

        #myQuery += ' from:'
        #myQuery += ' OR from:'.join(kwargs["authors"])
    #print(myQuery)
    import signal
    # Register the signal function handler
    signal.signal(signal.SIGALRM, __streamHandler__)
    # Define a timeout for your function
    signal.alarm(timeLimit)
    try:
       __stream__(stream,**kwargs)
    except Exception:
        print("Streaming over after time period of", timeLimit, "seconds... Retrieved", len(stream.listener.getTweets()), "tweets.")
        stream.disconnect()
    if authors and words:
        print("Filtering out tweets that don't contain the specified words...")
        myTweets=[]
        for tweet in stream.listener.getTweets():
            if 'full_text' in tweet:
                tweet['text'] = tweet['full_text']
                del (tweet['full_text'])
            if any(containsWord(tweet['text'],word) for word in words):
                myTweets.append(tweet)
        print("Done. Retrieved", len(myTweets), "tweets written by the authors specified and containing (any of) the words specified.")
        return myTweets
    return stream.listener.getTweets()


def saveTweets(tweets, collectionName, featuresToSave='all', onFile=False, onDb=True, dbName = 'tweets'):
    """ saves the input tweets into fileSystem(if onFile) or mongoDB(if onDb).
    collectionName relates to both directory name (in data/ folder) to save json files on fileSystem (if onFile) and collection name
    to save on mongoDB into specified dbName.
    :param: featuresToSave relates to the list of attributes to save for the input tweets. If 'all', then the list containing every attribute for each tweet will be saved. """

    filteredTweets = None
    #open a file to store the status objects
    if isinstance(featuresToSave, str):
        if featuresToSave.lower()=='all':
            filteredTweets = tweets

    if filteredTweets is None:
        featuresToSave = mapToValid(featuresToSave)
        if not all([any ([f in tweet for tweet in tweets]) for f in featuresToSave]):
            print("Invalid attribute specified in featuresToSave. Cannot save the tweets.")
            return False
        filteredTweets = [{feature: tweet[feature] if feature in tweet else None for feature in featuresToSave } for tweet in tweets]
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
        if (collectionName not in db.collection_names()):
            print("Cannot load tweets from db. No collections called: " + collectionName)
            return None
        for tweet in tweetCollection.find({}, {'_id': 0}):
            tweets.append(tweet)
        print("Done. Tweets correctly loaded")
        return tweets

    if fromDb:
        return loadFromDb()
    return loadFromFile()


def isRetweet(tweet):
    isRetweeted = False
    if 'retweeted' in tweet:
        isRetweeted = tweet['retweeted']
    textKey = None
    if "text" in tweet:
        textKey="text"
    elif "full_text" in tweet:
        textKey="full_text"
    else:
        raise Exception("Invalid tweet text")
    return tweet[textKey].startswith("RT ") or isRetweeted or "retweeted_status" in tweet


def mapToValid(queryAttribute):
    if queryAttribute is None or not queryAttribute:
        return []
    if not isinstance(queryAttribute, list):
        return list([queryAttribute])
    return queryAttribute
