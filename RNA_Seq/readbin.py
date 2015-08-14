#! /usr/bin/env python

#Script to categorize a read as exonic, intronic, 5' UTR, etc. based
#on its first read. Meant to go along with the percentages determined by
#the existing RNASeqAnalysis plugin, but based on number of reads, not 
#number of bases

import sys

#The star-bowtie aligned bam file of the run, converted to SAM format
samfile=open(sys.argv[1],'r')
#The reference file of known human transcripts, currently using /home/ionadmin/ariel/BED/refSeq.txt
reffile=open(sys.argv[2],'r')
#The file containing the read counts of various categories
outfile=open(sys.argv[3],'w')

transcriptReads=0
exonReads=0
utr3Reads=0
utr5Reads=0
intronReads=0
codingReads=0
noncodingReads=0
microReads=0

samline=samfile.readline().strip()
refline=reffile.readline().strip()
if refline[0]==">":
	refline=reffile.readline().strip()

#Parse through the sam file and reference file at
while samline!='' and refline!='':
	samlist=samline.split('\t')
	reflist=refline.split('\t')
	samChromosome=samlist[2]
	refChromosome=reflist[2]
	switchedchromosomes=False
	#First check to see if the chromosomes match
	if samChromosome==refChromosome:
		position=int(samlist[3])
		seq=len(samlist[9])
		endpoint=position+seq
		left=int(reflist[4])
		right=int(reflist[5])
		#Read is past the current transcript boundaries, need to switch to a later transcript
		if position>right:
			while position>right:
				refline=reffile.readline().strip()
				if refline!="":
					reflist=refline.split('\t')
					if reflist[2]!=refChromosome:
						break
					if reflist[2]==refChromosome:
						left=int(reflist[4])
						right=int(reflist[5])
				else:
					break
					left=100000000000000000000000000
					right=100000000000000000000000000
		#Read is upstream of the gene transcript, need to switch to later reads
		elif position<left:
			while position<left:
				samline=samfile.readline().strip()
				if samline!="":
					samlist=samline.split('\t')
					position=int(samlist[3])
					seq=len(samlist[9])
					endpoint=position+seq
				else:
					break
		#Check if reads are inside the boundaries of the transcript
		if left <= position <= right:
			transcriptReads+=1
			exonleft=reflist[9].split(',')
			exonright=reflist[10].split(',')
			found=False
			isEndpoint=False
			#Check all of the exons to see if the read is in an exonic region
			for i in range(len(exonleft)-1):
				newleft=int(exonleft[i])
				newright=int(exonright[i])
				if newleft<position<newright:
					found=True
			'''if found==False:
				for i in range(len(exonleft)-1):
					newleft=int(exonleft[i])
					newright=int(exonright[i])
					if newleft<endpoint<newright:
						found=True
						isEndpoint=True'''
			if found==True:
				exonReads+=1
				codingleft=int(reflist[6])
				codingright=int(reflist[7])
				#Check if the transcript has a coding region
				if codingleft==codingright:
					noncodingReads+=1
					genename=reflist[0]
					if genename[0:3]=="MIR":
						microReads+=1
				else:
					if isEndpoint==False:
						if codingleft<=position<=codingright:
							codingReads+=1
						elif position<codingleft:
							utr5Reads+=1
						elif codingright<position:
							utr3Reads+=1
					else:
						if codingleft<=endpoint<=codingright:
							codingReads+=1
						elif endpoint<codingleft:
							utr5Reads+=1
						elif codingright<endpoint:
							utr3Reads+=1
			else:
				intronReads+=1
	
	elif refChromosome!=samChromosome:
		switchedchromosomes=True
		if refChromosome<samChromosome:
			while refChromosome!=samChromosome:
				refline=reffile.readline().strip()
				if refline!="":
					reflist=refline.split('\t')
					refChromosome=reflist[2]
				else:
					break
		elif refChromosome>samChromosome:
			while refChromosome!=samChromosome:
				samline=samfile.readline().strip()			
				if samline!="":
					samlist=samline.split('\t')
					samChromosome=samlist[2]
				else:
					break
	if switchedchromosomes==False:
		samline=samfile.readline().strip()
	#exits if the while loop hit the end of either file
	if samline=="" or refline=="": 
		break


outfile.write("Transcripts: "+str(transcriptReads)+'\n')
outfile.write("Exons: "+str(exonReads)+'\n')
outfile.write("Introns: "+str(intronReads)+'\n')
outfile.write("5' UTR: "+str(utr5Reads)+'\n')
outfile.write("3' UTR: "+str(utr3Reads)+'\n')
outfile.write("Coding: "+str(codingReads)+'\n')
outfile.write("Non-coding: "+str(noncodingReads)+'\n')
outfile.write("MicroRNA: "+str(microReads))
