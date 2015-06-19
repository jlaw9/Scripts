#! /bin/bash

# Goal: Run samtools on the SEGA dataset to understand differences in variant calling between samtools, GATK, and TVC

# Author: Jeff Law

if [ "$#" -lt "3" ]; then
	echo "USAGE: bash run_samtools.sh </path/to/Bam> </path/to/BED> <Output_Dir>"
	exit 8
fi

BAM=$1
BED=$2
OUTPUT_DIR=$3
#WALES: /rawdata/support_files/BED/Wales/Merged/IAD000004_Amplicons_mergedDetail_noheader.bed
# I got these settings from these two websites: http://samtools.sourceforge.net/mpileup.shtml # https://www.edgebio.com/variant-calling-ion-torrent-data
# I also used the paper "Evaluation and optimisation of indel detection workflows for ion torrent sequencing of the BRCA1 and BRCA2 genes" (found at this link: http://www.biomedcentral.com/1471-2164/15/516)
# to help me know which settings o use and such. 
# -h 50 helps remove some of the homopolymer errors found in samtool's output

# original samtools command used
#samtools mpileup \
#	-uf /results/referenceLibrary/tmap-f3/hg19/hg19.fasta  \
#	-l $BED \
#	-h 50 \
#	$BAM \
#	| bcftools view -vcg - \
#	> $OUTPUT_DIR/samtools.vcf


# new and improved command with filtering.
samtools mpileup \
	-uf /results/referenceLibrary/tmap-f3/hg19/hg19.fasta  \
	-l $BED \
	-h 50 \
	-d 400 \
	-e 20 \
	-F 0.1 \
	-L 250 \
	-m 3 \
	-o 40 \
	$BAM \
	| bcftools view -vcg - \
	| vcfutils.pl varFilter \
	-d 15 \
	-D 400 \
	-a 2 \
	-w 3 \
	-W 10 \
	-1 0.0001 -2 1e-100 -3 0 -4 0.0001 \
	> $OUTPUT_DIR/samtools.vcf
#	| vcfutils.pl varFilter -D 400
# next, extract only the variants labelled as PASS and then report those.

#samtoools mpileup options.
# -d INT       max per-BAM depth to avoid excessive memory usage [250]

# SNP/INDEL genotype likelihoods options (effective with `-g' or `-u'):

#	-e INT       Phred-scaled gap extension seq error probability [20]
#	-F FLOAT     minimum fraction of gapped reads for candidates [0.002]
#	-h INT       coefficient for homopolymer errors [100]
#	-I           do not perform indel calling
#	-L INT       max per-sample depth for INDEL calling [250]
#	-m INT       minimum gapped reads for indel candidates [1]
#	-o INT       Phred-scaled gap open sequencing error probability [40]
#	-p           apply -m and -F per-sample to increase sensitivity
#	-P STR       comma separated list of platforms for indels [all]

# vcfutils.pl options
#Usage:   vcfutils.pl varFilter [options] <in.vcf>
#
#Options: -Q INT    minimum RMS mapping quality for SNPs [10]
#	-d INT    minimum read depth [2]
#	-D INT    maximum read depth [10000000]
#	-a INT    minimum number of alternate bases [2]
#	-w INT    SNP within INT bp around a gap to be filtered [3]
#	-W INT    window size for filtering adjacent gaps [10]
#	-1 FLOAT  min P-value for strand bias (given PV4) [0.0001]
#	-2 FLOAT  min P-value for baseQ bias [1e-100]
#	-3 FLOAT  min P-value for mapQ bias [0]
#	-4 FLOAT  min P-value for end distance bias [0.0001]
#	-e FLOAT  min P-value for HWE (plus F<0) [0.0001]
#	-p        print filtered variants
