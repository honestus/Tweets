import pandas as pd

def getNofNull(df,attributeName):
    return pd.isnull(df[attributeName]).sum()

def getPercentNull(df,attributeName):
    return getNofNull(attributeName)/len(df)

def getPercentValues(df,attributeName):
    return df.groupby(attributeName).size().apply(lambda x: float(x) / df.groupby(attributeName).size().sum()*100).sort_values(ascending=False)
