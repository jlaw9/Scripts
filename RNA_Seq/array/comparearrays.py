#! /usr/bin/env python2.7
import re
import sys

#This array compares the genearray files of two different runs, looks at the genes in a particular read count/percentage
#cell, and outputs a fraction representation of the shared genes in that cell over the total number of genes appearing in that cell

#For example: genearray/LN_Run1
array1=open(sys.argv[1],'r')
#For examplle: genearray/LN_Run2
array2=open(sys.argv[2],'r')
#For example: comparisonarray/LNRun1_by_LnRun2
outfile=open(sys.argv[3],'w')

array1dict={}
array2dict={}
outputarray={}

rowcount=0
for line in array1:
	rowcount+=1
	line=line.strip()
	lists=line.split('\t')
	columncount=0
	for item in lists:
		columncount+=1
		key=str(rowcount)+":"+str(columncount)
		array1dict[key]=item

row=0
for line in array2:
	row+=1
	line=line.strip()
	lists=line.split('\t')
	column=0
	for item in lists:
		column+=1
		key=str(row)+":"+str(column)
		array2dict[key]=item

for thing in array1dict:
	list1=array1dict[thing]
	list1=re.sub('[\[\]]','',list1)
	uno=list1.split(',')
	list2=array2dict[thing]
	list2=re.sub('[\[\]]','',list2)
	dos=list2.split(',')
	first=len(uno)
	second=len(dos)
	shared=0
	for item in uno:
		if item in dos:
			shared+=1
	total=first+second-shared
	pct=str(shared)+"/"+str(total)
	outputarray[thing]=pct

for i in range(11):
	for j in range(9):
		key=str(i+1)+":"+str(j+1)
		percentage=outputarray[key]
		outfile.write(str(percentage)+'\t')
	outfile.write('\n')

