def splitIntegerIntoIntegers(integer,numberOfIntervals):
    rest=integer%numberOfIntervals
    divisionResult=int(integer/numberOfIntervals)
    myList=[divisionResult]*(numberOfIntervals-rest)
    myList.extend([divisionResult+1]*rest)
    return myList
