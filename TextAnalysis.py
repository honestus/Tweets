import re, regex
import string

#nltk.download()
#nltk.download('punkt')
#nltk.download('wordnet')
#nltk.download('averaged_perceptron_tagger')
from nltk.corpus import stopwords

#global punctuationTbl, emoji_pattern

def findWholeWord(w):
    return re.compile(r'\b({})\b'.format(w), flags=re.IGNORECASE).search

def containsWord(text, word, irrelChars = [" ",".",",","?","!",":",";", "(", ")", "{", "}"]):
    "returns True if a word is contained in text, else False"
    word = word.strip().lower()
    text = text.strip().lower()

    if remove_emoticons(word)==word and remove_punctuation(word)==word:
    ### if the word is a simple word (doesn't contain any special characters (ie: punctuation, emoticons, hashtag))
        return findWholeWord(word)(text) is not None
    ### else check for simple matching in string by ignoring irrelevant neighbouring chars (to the searched word)
    ### eg: "#word" is contained in "#word." but it's not contained in "#worda"

    editedWord=""
    for c in word:
        if c in irrelChars:
            c="\\"+c
        editedWord+=c
    return bool(re.findall("[{}]".format("".join(irrelChars))+editedWord+"[{}]".format("".join(irrelChars)),text))

def remove_tags(text):
    import xml
    return ''.join(xml.etree.ElementTree.fromstring(text).itertext())

def remove_emoticons(text):
    if 'emoji_pattern' not in globals():
        global emoji_pattern
        emoji_pattern = re.compile("["
            u"\U0001F600-\U0001F64F"  # emoticons
            u"\U0001F300-\U0001F5FF"  # symbols & pictographs
            u"\U0001F680-\U0001F6FF"  # transport & map symbols
            u"\U0001F1E0-\U0001F1FF"  # flags (iOS)
                       "]+", flags=re.UNICODE)
    return emoji_pattern.sub(r'', text)

def remove_punctuation(text):
    import unicodedata
    import sys

    if 'punctuationTbl' not in globals():
        global punctuationTbl
        punctuationTbl = dict.fromkeys(i for i in range(sys.maxunicode)
                             if unicodedata.category(chr(i)).startswith('P'))
    return text.translate(punctuationTbl)

def text_clean(text):
    # method to remove repeated char, useless chars, etc.
    text = re.sub('http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', "", text) #remove URLS
    text = re.sub(r'(\W)(?=\1)', '', text.lower()) #reduces punctuation to max 1 consecutive punctuation char
    text = re.sub(r'(.)\1+', r'\1\1', text) #reduces to max 2 consecutive equal characters in the string
    return text


def text_preprocess(text, nGrams=[], stopWords = set(stopwords.words("english"))):
    """ Method to preprocess text. With respect to text_clean, it's useful for feature extraction starting from a text.
    It keeps track of stem, lemma and pos tag of every single word of the original text; it will also keep track of the emoticons.
    You can also recover nGrams from the text, by using a list of integers referring the nGrams you want to recover
    (eg: [2,3] will recover all the bigrams and trigrams)
    Every stopword is removed from the text; if you would like to keep every word of the original texts,
    you may simply have to use an empty list as the stopword list. """

    from nltk.stem import PorterStemmer, WordNetLemmatizer
    from nltk.tokenize import word_tokenize
    from nltk import ngrams, pos_tag
    from nltk import wordnet
    features, words, cleanedText = {}, {}, ""

    def get_emoticons(text):
        return regex.findall(r'\p{So}\p{Sk}*',string=text) #splits multiple emo into single ones
        #message_emojies=regex.findall(r'.\p{Sk}+|\X', string=tmpString)
        #returns a list containing all the SINGLE emos found in the message



    def get_wordnet_pos(treebank_tag):
        if treebank_tag in ['VB', 'VBD', 'VBG', 'VBN', 'VBP', 'VBZ']:
            return wordnet.wordnet.VERB
        elif treebank_tag in ['JJ', 'JJR', 'JJS']:
            return wordnet.wordnet.ADJ
        elif treebank_tag in ['RB', 'RBR', 'RBS', 'WRB']:
            return wordnet.wordnet.ADV
        else:
            return wordnet.wordnet.NOUN

    def getNGrams(n, orderedWords):
        nGrams = []
        for ngram in ngrams(orderedWords, n):
            nGrams.append ( "_".join(word for word in ngram))
        return nGrams

    features['emoticons']=get_emoticons(text)
    text = remove_emoticons(text)

    #words in original form and their posTag in the sentence
    splittedWords = word_tokenize(text)
    taggedWords = pos_tag(splittedWords)
    #removing stopwords and punctuation from the list of the original words
    validWords = list(word for word in taggedWords if word[0] not in stopWords)

    #stemming and lemming
    ps = PorterStemmer()
    lm = WordNetLemmatizer()
    finalWords = []
    for word in validWords:
        rmvPunct = word[0].strip(string.punctuation)
        if len(rmvPunct) > 0:
            updatedTag = get_wordnet_pos(word[1])
            newWord=(rmvPunct,updatedTag,ps.stem(rmvPunct),lm.lemmatize(word=rmvPunct, pos=updatedTag))
            finalWords.append(newWord)

    features['words']=finalWords

    if nGrams:
        nGramsFound = []
        for n in nGrams:
            nGramsFound.extend(getNGrams(n, orderedWords=[word[0] for word in finalWords]))
        features['nGrams'] = nGramsFound
    return features


#Bow representation
def getBow(corpusFeatures, asBoolean=True, useNGrams = False):
    bow = {}
    origWordsDict, stemWordsDict, lemWordsDict, emoDict, nGramDict = {}, {}, {}, {}, {}

    for i in range(len(corpusFeatures)):
        wordFeatures = corpusFeatures[i]['words']
        origWords = list(feat[0] for feat in wordFeatures)
        stemWords = list(feat[2] for feat in wordFeatures)
        lemWords = list(feat[3] for feat in wordFeatures)

        for w in origWords:
            if w not in origWordsDict:
                origWordsDict[w]=[0]*len(corpusFeatures)
            if asBoolean:
                origWordsDict[w][i]=1
            else:
                origWordsDict[w][i]+=1
        for w in stemWords:
            if w not in stemWordsDict:
                stemWordsDict[w]=[0]*len(corpusFeatures)
            if asBoolean:
                stemWordsDict[w][i]=1
            else:
                stemWordsDict[w][i]+=1
        for w in lemWords:
            if w not in lemWordsDict:
                lemWordsDict[w]=[0]*len(corpusFeatures)
            if asBoolean:
                lemWordsDict[w][i]=1
            else:
                lemWordsDict[w][i]+=1

        emoticons = corpusFeatures[i]['emoticons']
        for emo in emoticons:
            if emo not in emoDict:
                emoDict[emo]=[0]*len(corpusFeatures)
            if asBoolean:
                emoDict[emo][i]=1
            else:
                emoDict[emo][i]+=1

        if useNGrams:
            try:
                nGrams = corpusFeatures[i]['nGrams']
                for nGram in nGrams:
                    if nGram not in nGramDict:
                        nGramDict[nGram]=[0]*len(corpusFeatures)
                    if asBoolean:
                        nGramDict[nGram][i]=1
                    else:
                        nGramDict[nGram][i]+=1
            except KeyError:
                print("No nGrams found in the features")


        bow['origWords'] = origWordsDict
        bow['stems'] = stemWordsDict
        bow['lemmas'] = lemWordsDict
        bow['emoticons'] = emoDict
        bow['nGrams'] = nGramDict
    return bow


def getUpdatedTextsTfIdf(features, typeOfWords='origWords',useEmo=True,useNGrams=True):
    updatedTexts = []
    for docFeatures in features:
        if typeOfWords == 'origWords':
            updatedText = ' '.join(list(feat[0] for feat in docFeatures['words']))
        elif typeOfWords == 'stems':
            updatedText = ' '.join(list(feat[2] for feat in docFeatures['words']))
        elif typeOfWords == 'lemmas':
            updatedText = ' '.join(list(feat[3] for feat in docFeatures['words']))
        else:
            print('uncorrect type of words.')
            return

        if useEmo:
            updatedText += ' ' + ' '.join([emo for emo in docFeatures['emoticons']])
        if useNGrams:
            updatedText += ' ' + ' '.join([nGram for nGram in docFeatures['nGrams']])
        updatedTexts.append(updatedText)

    return updatedTexts


def getTopNWords(bow, n=50,typeOfWords='origWords', useEmo=True, keepNumber=True):
    allWordsCount = {}
    for word in bow[typeOfWords].keys():
        allWordsCount[word] = sum(bow[typeOfWords][word])
    if useEmo:
        for emo in bow['emoticons'].keys():
            allWordsCount[emo] = sum(bow['emoticons'][emo])

    if keepNumber:
        return [(k, allWordsCount[k]) for k in sorted(allWordsCount, key=allWordsCount.get, reverse=True)[:n]]

    def sortedMethod(k):
        return allWordsCount[k]
    return sorted(allWordsCount, key=sortedMethod, reverse=True)[:n]


def getSatisfyingTweets(word,origBow,minN=1,wordType='origWords'):
    #gives the list of all the tweets containing the word in input, as minimum minN times
    #it returns a dict having as key the tweet Id(in the df) and as value the n° of times the word occur in that tweet
    from numpy import array
    wordRepres = array(origBow[wordType][word])
    boolRepres = wordRepres >= minN
    tmpArr = array(range(len(boolRepres)))[boolRepres]
    return [(i,wordRepres[i]) for i in tmpArr]
