import re, regex, xml
import nltk
import string

#nltk.download()
#nltk.download('punkt')
#nltk.download('wordnet')
#nltk.download('averaged_perceptron_tagger')
from nltk.corpus import stopwords
from nltk.stem import PorterStemmer, WordNetLemmatizer
from nltk.tokenize import sent_tokenize, word_tokenize


def remove_tags(text):
    return ''.join(xml.etree.ElementTree.fromstring(text).itertext())


def text_clean(text):
    # method to remove repeated char, useless chars, etc.
    text = re.sub('http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', "", text) #remove URLS
    text = re.sub(r'(\W)(?=\1)', '', text.lower()) #reduces punctuation to max 1 consecutive punctuation char
    text = re.sub(r'(.)\1+', r'\1\1', text) #reduces to max 2 consecutive equal characters in the string
    return text


def text_preprocess(text, nGrams=[], stopWords = set(stopwords.words("english"))):
    #method to preprocess text. With respect to text_clean, it's useful for feature extraction starting from a text.
    #If removeStop is set to True, it will remove every stopword from the text
    #stem can assume value=1 if you want to use porterStemmer and =2 if you want to use wordnetLemmatizer
    features, words, cleanedText = {}, {}, ""

    def get_emoticons():
        return regex.findall(r'\p{So}\p{Sk}*',string=text) #splits multiple emo into single ones
        #message_emojies=regex.findall(r'.\p{Sk}+|\X', string=tmpString)
        #returns a list containing all the SINGLE emos found in the message

    def remove_emoticons(text=text):
        emoji_pattern = re.compile("["
            u"\U0001F600-\U0001F64F"  # emoticons
            u"\U0001F300-\U0001F5FF"  # symbols & pictographs
            u"\U0001F680-\U0001F6FF"  # transport & map symbols
            u"\U0001F1E0-\U0001F1FF"  # flags (iOS)
                           "]+", flags=re.UNICODE)
        return emoji_pattern.sub(r'', text)

    def remove_punctuation(text=text):
        import unicodedata
        import sys

        tbl = dict.fromkeys(i for i in range(sys.maxunicode)
                                 if unicodedata.category(chr(i)).startswith('P'))
        return text.translate(tbl)

    def get_wordnet_pos(treebank_tag):
        if treebank_tag in ['VB', 'VBD', 'VBG', 'VBN', 'VBP', 'VBZ']:
            return nltk.wordnet.wordnet.VERB
        elif treebank_tag in ['JJ', 'JJR', 'JJS']:
            return nltk.wordnet.wordnet.ADJ
        elif treebank_tag in ['RB', 'RBR', 'RBS', 'WRB']:
            return nltk.wordnet.wordnet.ADV
        else:
            return nltk.wordnet.wordnet.NOUN

    def getNGrams(n, orderedWords):
        from nltk import ngrams

        nGrams = []
        for ngram in ngrams(orderedWords, n):
            nGrams.append ( "_".join(word for word in ngram))
        return nGrams

    features['emoticons']=get_emoticons()
    text = remove_emoticons()

    #words in original form and their posTag in the sentence
    splittedWords = word_tokenize(text)
    taggedWords = nltk.pos_tag(splittedWords)
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
            if not w in origWordsDict:
                origWordsDict[w]=[0]*len(corpusFeatures)
            if asBoolean:
                origWordsDict[w][i]=1
            else:
                origWordsDict[w][i]+=1
        for w in stemWords:
            if not w in stemWordsDict:
                stemWordsDict[w]=[0]*len(corpusFeatures)
            if asBoolean:
                stemWordsDict[w][i]=1
            else:
                stemWordsDict[w][i]+=1
        for w in lemWords:
            if not w in lemWordsDict:
                lemWordsDict[w]=[0]*len(corpusFeatures)
            if asBoolean:
                lemWordsDict[w][i]=1
            else:
                lemWordsDict[w][i]+=1

        emoticons = corpusFeatures[i]['emoticons']
        for emo in emoticons:
            if not emo in emoDict:
                emoDict[emo]=[0]*len(corpusFeatures)
            if asBoolean:
                emoDict[emo][i]=1
            else:
                emoDict[emo][i]+=1

        if useNGrams:
            try:
                nGrams = corpusFeatures[i]['nGrams']
                for nGram in nGrams:
                    if not nGram in nGramDict:
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
    wordRepres = np.array(origBow[wordType][word])
    boolRepres = wordRepres >= minN
    tmpArr = np.array(range(len(boolRepres)))[boolRepres]
    return [(i,wordRepres[i]) for i in tmpArr]
