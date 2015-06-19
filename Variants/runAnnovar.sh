#! /bin/bash

#$ -S /bin/bash
#$ -cwd
#$ -N Wales_Annovar
#$ -o wales_anno.log
#$ -e wales_anno_progress_err.log
#$ -q all.q
#$ -V

if [ $# -lt 2 ]; then
	echo "USAGE: runAnnovar.sh <path/to/.vcf> <path/to/outfile>"
	exit 8
fi

echo "$1 beginning annovar at `date`" 
echo "$1 beginning annovar `date`" 1>&2


# this gives table output
# Annotate the somatic variants with table annovar. 
# I know we updated some of the annovar code in the file /home/ionadmin//TRI_Scripts/annovar/annotate_variation.pl starting on line 1552
/home/ionadmin//TRI_Scripts/annovar/convert2annovar.pl --format vcf4old --snpqual 0 $1 > $2.vcf
/home/ionadmin//TRI_Scripts/annovar/table_annovar.pl \
	$2.vcf \
	/rawdata/software/annovar/humandb_ucsc/ \
	--outfile $2 \
	--buildver hg19 \
	--protocol refGene,1000g2012apr_all,snp129NonFlagged,snp137NonFlagged,cosmic68,ljb23_all \
	--operation g,f,f,f,f,f \
	--remove \
	--nastring . 

rm $2.vcf

# this will give you VCF output
#/home/ionadmin/TRI_Scripts/annovar/table_annovar.pl \
#	$1 \
#	/rawdata/software/annovar/humandb_ucsc/ \
#	--outfile $2 \
#	--buildver hg19 \
#	--vcfinput \
#	--protocol refGene,1000g2012apr_all,ljb23_all,snp129NonFlagged,snp137NonFlagged \
#	--operation g,f,f,f,f \
#	--remove

if [ $? -ne 0 ]; then
	echo "$1 ERROR!! Annovar did not run correctly"
fi

echo "$1 finished annovar `date`" 
echo "$1 finished annovar `date`" 1>&2
