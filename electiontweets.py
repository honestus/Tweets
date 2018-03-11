
# coding: utf-8

# In[1]:

import tweepy, json, pymongo
import pandas as pd
import numpy as np
from twitterscraper import *
from TextAnalysis import *


# In[7]:

# retrieving previously saved tweets from json file
with open('data/electiontweets.json') as json_data:
    electionTweets = json.load(json_data)

electionTweetsDf = pd.DataFrame.from_dict(electionTweets)


# In[9]:

from unidecode import unidecode

texts = list(electionTweetsDf['text'])
cleanedTexts = list(map(lambda x: text_clean(unidecode(x)),texts))

electionTweetsDf['clean_text'] = cleanedTexts
features = list(map(lambda x: text_preprocess(x), cleanedTexts))


# In[11]:

bow = getBow(features,asBoolean=False)


# In[12]:

#gives the list of all the tweets containing the word in input, as minimum minN times
#it returns a dict having as key the tweet Id(in the df) and as value the n° of times the word occur in that tweet
def getSatisfyingTweets(word,minN=1,origBow=bow,wordType='origWords'):
    wordRepres = np.array(origBow[wordType][word])
    boolRepres = wordRepres >= minN
    tmpArr = np.array(range(len(boolRepres)))[boolRepres]
    return {i:wordRepres[i] for i in tmpArr}
    


# In[14]:

sat = getSatisfyingTweets('america',minN=1)
sat


# In[15]:

topStems = getTopNWords(bow=bow,keepNumber=False,n=50,typeOfWords='stems',useEmo=True)
topStems


# In[34]:

#Defining a new dataframe as bow representation(matrix term-tweet)
bowDf = pd.DataFrame(data={x: bow['stems'][x] for x in topStems})
bowDf


# In[58]:

from sklearn.decomposition import PCA
from matplotlib import pyplot as plt
from bokeh.models import ColumnDataSource, HoverTool
from bokeh.plotting import figure, show, output_file
pca = PCA(n_components=0.5)
pca.fit(bowDf)
pcscores = pd.DataFrame(pca.transform(bowDf))
pcscores.columns = ['PC' + str(i + 1) for i in range(pcscores.shape[1])]
loadings = pd.DataFrame(pca.components_, columns=list(bowDf.columns))
load_squared = loadings.transpose() ** 2
load_squared.columns = ['PC' + str(i + 1) for i in range(pcscores.shape[1])]


# In[65]:

loadings.index = ['PC'+str(j+1) for j in range(len(loadings))]

# loadings = loadings.iloc[0:30, :]  # Use only a subset of the data
#loadings = loadings.transpose()  # Use rotation

words = loadings.columns.tolist()
pc_names = loadings.index.tolist()


xname = []
yname = []
color = []
alpha = []
for i, pc in enumerate(pc_names):
    for j, word in enumerate(words):
        xname.append(word)
        yname.append(pc)

        alpha.append(min(loadings.iloc[i, j]**2, 0.9)+0.1)  # Transparency is square of loading factor

        # Color denotes sign of loading factor
        if loadings.iloc[i, j] > 0:
            color_to_use = '#5ab4ac'
        else:
            color_to_use = '#d8b365'

        if abs(loadings.iloc[i, j]) < 0.1:
            color_to_use = '#f5f5f5'

        color.append(color_to_use)

source = ColumnDataSource(data=dict(
    xname=xname,
    yname=yname,
    colors=color,
    alphas=alpha,
    count=loadings.values.flatten(),
))

p = figure(title="PCA Loading Factors",
           x_axis_location="above", tools="pan,wheel_zoom,box_zoom,reset,hover,save",
           x_range=words, y_range=list(reversed(pc_names)))

p.plot_width = 1000
p.plot_height = 1000
p.grid.grid_line_color = None
p.axis.axis_line_color = None
p.axis.major_tick_line_color = None
p.axis.major_label_text_font_size = "8pt"
p.axis.major_label_standoff = 0
p.xaxis.major_label_orientation = np.pi / 3

p.rect('xname', 'yname', 0.9, 0.9, source=source,
       color='colors', alpha='alphas', line_color=None)

p.select_one(HoverTool).tooltips = [
    ('pc/word', '@yname, @xname'),
    ('factor', '@count'),
]

show(p)

