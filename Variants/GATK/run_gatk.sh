#! /bin/bash

# Goal: Run GATK on the SEGA dataset to understand differences in variant calling between samtools, GATK, and TVC

# Author: Jeff Law

if [ "$#" -lt "3" ]; then
	echo "USAGE: bash run_gatk.sh </path/to/Bam> </path/to/BED> <Output_Dir>"
	exit 8
fi

BAM=$1
BED=$2
OUTPUT_DIR=$3
GATK="/results/plugins/variantCaller/TVC/jar/GenomeAnalysisTK.jar"
# Can't run the newest version of GATK because it requires java v1.7
#GATK="/rawdata/software/GenomeAnalysisTK-3.2-2/GenomeAnalysisTK.jar"
#WALES: /rawdata/support_files/BED/Wales/Merged/IAD000004_Amplicons_mergedDetail_noheader.bed
# I got these settings from the GATK best practices manual found online at: 
#https://www.broadinstitute.org/gatk/guide/best-practices?bpm=DNAseq#methods_vqsr39

mkdir -p $OUTPUT_DIR

java -jar $GATK \
	-T UnifiedGenotyper \
	-R /results/referenceLibrary/tmap-f3/hg19/hg19.fasta \
	-I $BAM \
	-o $OUTPUT_DIR/gatk_unified.raw.vcf \
	-stand_call_conf 10.0 \
	-stand_emit_conf 10.0 \
	-L $BED \
	--genotyping_mode DISCOVERY \
	--output_mode EMIT_VARIANTS_ONLY

# Hard filter explanation also found on the GATK best practices guide

java -jar $GATK \
	-T SelectVariants \
	-R /results/referenceLibrary/tmap-f3/hg19/hg19.fasta \
	-V $OUTPUT_DIR/gatk_unified.raw.vcf \
	-selectType SNP  \
	-o $OUTPUT_DIR/gatk_unified_snps_only.raw.vcf

java -jar $GATK \
	-T VariantFiltration \
	-R /results/referenceLibrary/tmap-f3/hg19/hg19.fasta \
	-V $OUTPUT_DIR/gatk_unified_snps_only.raw.vcf \
	--filterExpression "QD < 2.0 || FS > 60.0 || MQ < 40.0 || MQRankSum < -12.5 || ReadPosRankSum < -8.0 || DP < 15" \
	--filterName "my_snp_filter" \
	-o $OUTPUT_DIR/gatk_snps.vcf 

grep -v "my_snp_filter" $OUTPUT_DIR/gatk_snps.vcf > $OUTPUT_DIR/gatk_filtered_snps.vcf 

java -jar $GATK \
	-T SelectVariants \
	-R /results/referenceLibrary/tmap-f3/hg19/hg19.fasta \
	-V $OUTPUT_DIR/gatk_unified.raw.vcf \
	-selectType INDEL  \
	-o $OUTPUT_DIR/gatk_unified_indels_only.raw.vcf

	# for some reason, the -L 20 option was giving an error for SelectVaiants INDEL
	#-L 20 \

java -jar $GATK \
	-T VariantFiltration \
	-R /results/referenceLibrary/tmap-f3/hg19/hg19.fasta \
	-V $OUTPUT_DIR/gatk_unified_indels_only.raw.vcf \
	--filterExpression "QD < 2.0 || FS > 200.0 || ReadPosRankSum < -20.0 || DP < 15" \
	--filterName "my_indel_filter" \
	-o $OUTPUT_DIR/gatk_filtered_indels.vcf 

# delete the temp files
rm $OUTPUT_DIR/gatk_unified.raw.vcf*
rm $OUTPUT_DIR/gatk_unified_snps_only.raw.vcf*
#rm $OUTPUT_DIR/gatk_unified_indels_only.raw.vcf*
