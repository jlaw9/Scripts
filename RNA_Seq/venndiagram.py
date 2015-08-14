#! /usr/bin/env python
import sys

#Read count list of one sample, can be found at /mnt/Despina/projects/RNA_Seq/PNET/A_204/Run1/Analysis_Files/RNA ... .genereads.xls
file1=open(sys.argv[1],'r')
#Read count list of other sample
file2=open(sys.argv[2],'r')
#File of venn diagram with hard cutoff (both genes need to have >1000 reads to be counted as shared)
hardfile=open(sys.argv[3],'w')
#File of venn diagram with soft cutoff (one gene has to have >1000 and the other has to have >750 to count as shared)
softfile=open(sys.argv[4],'w')

list1=[]
softlist1=[]
list2=[]
softlist2=[]
hardshared=[]
hard1=[]
hard2=[]
softshared=[]
exclusiveto1=[]
exclusiveto2=[]

#Find genes with >1000 and 750-1000, append to two different lists: list1 and softlist1
for line in file1:
	line=line.strip()
	line=line.split('\t')
	if line[1]=='Reads':
		reads=0
	else:
		reads=float(line[1])
	if reads>1000:
		gene=line[0]
		list1.append(gene)
	elif reads>750:
		gene=line[0]
		softlist1.append(gene)

#Find genes with >1000 and 750-1000, append to two different lists: list2 and softlist2
for line in file2:
	line=line.strip()
	line=line.split('\t')
	if line[1]=='Reads':
		reads=0
	else:
		reads=float(line[1])
	if reads>1000:
		gene=line[0]
		list2.append(gene)
	elif reads>750:
		gene=line[0]
		softlist2.append(gene)

#Iterate through items in list1, determine if they're on list2 or softlist2 or neither
for item in list1:
	if item in list2:
		hardshared.append(item)
		softshared.append(item)
	elif item in softlist2:
		softshared.append(item)
		hard1.append(item)
	else:
		exclusiveto1.append(item)
		hard1.append(item)
#Iterate through items in list2 but not in list1, determine if they're on softlist1
for thing in list2:
	if thing not in list1:
		if thing not in softlist1:
			exclusiveto2.append(thing)
			hard2.append(thing)
		else:
			softshared.append(thing)
			hard2.append(thing)

hardfile.write(str(len(hard1))+'\t'+str(hard1)+"\n")
hardfile.write(str(len(hardshared))+'\t'+str(hardshared)+"\n")
hardfile.write(str(len(hard2))+'\t'+str(hard2)+"\n")

softfile.write(str(len(exclusiveto1))+'\t'+str(exclusiveto1)+'\n')
softfile.write(str(len(softshared))+'\t'+str(softshared)+"\n")
softfile.write(str(len(exclusiveto2))+'\t'+str(exclusiveto2)+'\n')
