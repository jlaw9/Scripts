#! /usr/bin/env python2.7
import sys

#Read count, available in Analysis_Files/RNA ... .genereads.xls
reads=open(sys.argv[1],'r')
#Percentages count, made by running run count through percentages.py
percentages=open(sys.argv[2],'r')
#genecounts/LN_Run1
outfile=open(sys.argv[3],'w')

readdict={}
pctdict={}

#Cutoffs for the percentages, on a semi-logarithmic scale
pcts=['<.00000003','<.0000001','<.0000003','<.000001','<.000003','<.00001','<.00003','<.0001','<.0003','<.001','more']
percents=[]

for item in pcts:
	readdictionary={}
	percents.append(readdictionary)

for line in reads:
	line=line.strip()
	line=line.split('\t')
	if line[1]!="Reads":
		num=int(line[1])
		gene=line[0]
		readdict[gene]=num

for line in percentages:
	line=line.strip()
	line=line.split('\t')
	num=float(line[1])
	gene=line[0]
	pctdict[gene]=num

for item in pctdict:
	dictionary={}
	#determines which row of the array the gene goes in
	percent=pctdict[item]
	if percent <=.00000003:
		dictionary=percents[0]	
	elif percent >.00000003 and percent <=.0000001:
		dictionary=percents[1]
	elif percent >.0000001 and percent <=.0000003:
		dictionary=percents[2]
	elif percent >.0000003 and percent <=.000001:
		dictionary=percents[3]
	elif percent >.000001 and percent<=.000003:
		dictionary=percents[4]
	elif percent >.000003 and percent<=.00001:
		dictionary=percents[5]
	elif percent >.00001 and percent<=.00003:
		dictionary=percents[6]
	elif percent >.00003 and percent<=.0001:
		dictionary=percents[7]
	elif percent >.0001 and percent<=.0003:
		dictionary=percents[8]
	elif percent >.0003 and percent<=.001:
		dictionary=percents[9]
	elif percent >.001:
		dictionary=percents[10]

	#determines the column of the row the gene goes in
	count=readdict[item]
	if count<=10:
		if '<10' not in dictionary:
			dictionary['<10']=1
		else:
			dictionary['<10']+=1
	elif count>10 and count<=30:
		if '11-30' not in dictionary:
			dictionary['11-30']=1
		else:
			dictionary['11-30']+=1
	elif count>30 and count<=100:
		if '31-100' not in dictionary:
			dictionary['31-100']=1
		else:
			dictionary['31-100']+=1
	elif count>100 and count<=300:
		if '101-300' not in dictionary:
			dictionary['101-300']=1
		else:
			dictionary['101-300']+=1
	elif count>300 and count<=1000:
		if '301-1000' not in dictionary:
			dictionary['301-1000']=1
		else:
			dictionary['301-1000']+=1
	elif count>1000 and count<=3000:
		if '1001-3000' not in dictionary:
			dictionary['1001-3000']=1
		else:
			dictionary['1001-3000']+=1
	elif count>3000 and count<=10000:
		if '3001-10000' not in dictionary:
			dictionary['3001-10000']=1
		else:
			dictionary['3001-10000']+=1
	elif count>10000 and count<=30000:
		if '10001-30000' not in dictionary:
			dictionary['10001-30000']=1
		else:
			dictionary['10001-30000']+=1
	elif count>30000:
		if '30001+' not in dictionary:
			dictionary['30001+']=1
		else:
			dictionary['30001+']+=1

for item in percents:
	if '<10' not in item:
		item['<10']=0
	if '11-30' not in item:
		item['11-30']=0
	if '31-100' not in item:
		item['31-100']=0 
	if '101-300' not in item:
		item['101-300']=0
	if '301-1000' not in item:
		item['301-1000']=0 
	if '1001-3000' not in item:
		item['1001-3000']=0
	if '3001-10000' not in item:
		item['3001-10000']=0 
	if '10001-30000' not in item:
		item['10001-30000']=0
	if '30001+' not in item:
		item['30001+']=0

for item in percents:
	A=item['<10']
	B=item['11-30']
	C=item['31-100']
	D=item['101-300']
	E=item['301-1000']
	F=item['1001-3000']
	G=item['3001-10000']
	H=item['10001-30000']
	I=item['30001+']
	outfile.write(str(A)+'\t'+str(B)+'\t'+str(C)+'\t'+str(D)+'\t'+str(E)+'\t'+str(F)+'\t'+str(G)+'\t'+str(H)+'\t'+str(I)+'\n')

