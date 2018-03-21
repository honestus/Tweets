#!/bin/sh
arr=($@)
readonly numOfWords=$1
readonly numOfAuthors=$2

if [ $numOfWords -gt 0 ]
then
  words=${arr[2]}
  for i in $(seq 3 $((numOfWords+1)))
  do
    words=$words" OR "${arr[i]}
  done
fi

if [ $numOfAuthors -gt 0 ]
then
  authors="from%3A"${arr[$((numOfWords+2))]}
  for i in $(seq $((numOfWords+3)) $((numOfWords+numOfAuthors+1)))
  do
    authors=$authors" OR from%3A"${arr[i]}
  done
fi

index=$(($numOfWords+$numOfAuthors+2))

if [ ${arr[index]} == '-sd' ]
then
  index=$((index+1))
  startingDate="since%3A"${arr[index]}
  index=$((index+1))
fi

if [ ${arr[index]} == '-ed' ]
then
  index=$((index+1))
  endingDate="until%3A"${arr[index]}
  index=$((index+1))
fi

outputFile=${arr[index]}

twitterscraper \"$words $authors $startingDate $endingDate\" -o $outputFile
