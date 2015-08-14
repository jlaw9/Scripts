#! /usr/bin/env python2.7
import sys

##This script takes the read counts of each gene in a run, and translates that into
##a percentage of the total number of gene reads. This is intended as a transformation
##to see differential expression when total reads vary so widely (for instance for the same
##sample with a 85 million read run and a 50 million read run, a gene could have 500
##more reads in the larger sample but have similar actual expression.

#Can be found in /mnt/Despina/projects/RNA_Seq/PNET/A_204/Run1/Analysis_Files/RNA_barcode... .genereads.xls
readsfile=open(sys.argv[1],'r')
#A text file with the gene name and the percentage of expression 
outfile=open(sys.argv[2],'w')

for line in readsfile:
	line=line.strip()
	line=line.split('\t')
	if line[1]!="Reads":
		number=float(line[1])
		pct=number/counter
		percent='{0:6.9f}'.format(pct)
		outfile.write(line[0]+'\t'+str(percent)+'\n')

