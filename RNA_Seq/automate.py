#! /usr/bin/env python2.7
import os
import subprocess
import sys
import re

spreadsheet=open(sys.argv[2],'a')

#filename is the BAM file in /mnt/Despina/Projects/RNA_Seq directory
filename=sys.argv[1]
linedict={}
mntDir=os.path.dirname(os.path.realpath(filename))

##Check for a sam file in the directory
hasSAM=False
os.chdir(mntDir)
for j in os.listdir(os.getcwd()):
	if j.endswith(".sam"):
		hasSAM=True
		samfile=os.path.realpath(j)
if hasSAM==False:
	os.system("samtools view %s > starbowtie.sam" % (filename))
	samfile=os.path.realpath("starbowtie.sam")


##Get run summary stats from analysis file, store them as a dictionary
if os.path.exists("Analysis_Files"):
	os.chdir("Analysis_Files")
	for i in os.listdir(os.getcwd()):
		if i.endswith(".stats.txt"):
			statsfile=open(i,'r')
			for line in statsfile:
				if line!='' and line!="\n" and line!="RNASeqAnalysis Summary Report\n":
					spl=line.strip().split(":")
					spl[1]=re.sub(" ","",spl[1])
					linedict[spl[0]]=spl[1]
			ilist=i.split("_")
			year=ilist[5]
			month=ilist[6]
			day=ilist[7]
			date=month+'/'+day+'/'+year
			for item in ilist:
				if item[0:3]=="PLU" or item[0:3]=="MER":
					item=re.sub("-PNET","",item)
					runID=item
					break

##Get summary stat values from dictionary
totalReads=int(linedict["Total Reads"])
alignedReads=int(linedict["Aligned Reads"])
pctReads=linedict["Pct Aligned"]
meanLength=float(linedict["Mean Read Length"])
readsMapped=int(linedict["Reads Mapped to Genes"])
morethan10=int(linedict["Genes with 10+ reads"])
morethan100=int(linedict["Genes with 100+ reads"])
morethan1000=int(linedict["Genes with 1000+ reads"])
morethan10000=int(linedict["Genes with 10000+ reads"])
isoforms=int(linedict["Isoforms Detected"])
totalBases=int(linedict["Total Base Reads"])
alignedBases=int(linedict['Total Aligned Bases'])
pctBases=linedict['Pct Aligned Bases']
pctCoding=linedict['Pct Coding Bases']
pctUTR=linedict['Pct UTR Bases']
pctRibosomal=linedict['Pct Ribosomal Bases']
pctIntronic=linedict['Pct Intronic Bases']
pctIntergenic=linedict['Pct Intergenic Bases']
strandBalance=float(linedict['Strand Balance'])


##Run script to bin reads
os.chdir("/home/ionadmin/ariel")
name=filename.split("/")
output=name[-3]+"_"+name[-2]
sample=name[-3]
run=re.sub("Run",'',name[-2])
thing2="BED/refSeq.txt"
subprocess.call("./readbin.py %s %s %s" % (samfile,thing2,output), shell=True)

##Obtain read count information from readbin.py's output
binned=open(output,'r')
line=binned.readline().strip()
linelist=line.split(":")
transcripts=int(linelist[1])
line=binned.readline().strip()
linelist=line.split(":")
exons=int(linelist[1])
exonic=float(exons)/float(transcripts)
line=binned.readline().strip()
linelist=line.split(":")
introns=int(linelist[1])
intronic=float(introns)/float(transcripts)
line=binned.readline().strip()
linelist=line.split(":")
fiveprime=int(linelist[1])
line=binned.readline().strip()
linelist=line.split(":")
threeprime=int(linelist[1])
cincoprime=float(fiveprime)/float(threeprime+fiveprime)
tresprime=float(threeprime)/float(threeprime+fiveprime)
line=binned.readline().strip()
linelist=line.split(":")
coding=int(linelist[1])
line=binned.readline().strip()
linelist=line.split(":")
noncoding=int(linelist[1])
line=binned.readline().strip()
linelist=line.split(":")
micro=int(linelist[1])
pctMicro=float(micro)/float(noncoding)

##Add run information to spreadsheet
spreadsheet.write(sample+'\t'+run+'\t'+runID+'\t'+date+'\t'+str(totalReads)+'\t')
spreadsheet.write(str(alignedReads)+'\t'+pctReads+'\t'+str(meanLength)+'\t')
spreadsheet.write(str(readsMapped)+'\t'+str(morethan10)+'\t'+str(morethan1000)+'\t')
spreadsheet.write(str(morethan10000)+'\t'+"230756"+'\t'+str(isoforms)+'\t'+str(totalBases)+"\t")
spreadsheet.write(str(alignedBases)+'\t'+pctBases+'\t'+pctCoding+'\t'+pctUTR+'\t')
spreadsheet.write(pctRibosomal+'\t'+pctIntronic+'\t'+pctIntergenic+'\t'+str(strandBalance)+'\t')
spreadsheet.write(str(transcripts)+'\t'+str(introns)+'\t'+str(exons)+'\t')
spreadsheet.write(str(exonic)+'\t'+str(intronic)+'\t'+str(fiveprime)+'\t'+str(threeprime)+'\t')
spreadsheet.write(str(cincoprime)+'\t'+str(tresprime)+'\t'+str(coding)+'\t'+str(noncoding)+'\t')
spreadsheet.write(str(micro)+'\t'+str(pctMicro)+'\n')
