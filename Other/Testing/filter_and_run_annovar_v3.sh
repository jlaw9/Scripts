#! /bin/bash

# Goal: Generate a spreadsheet that has all of the variants for all of the samples.
# Overview: 1) Generate a subset bed file using the cov.xls where the amplicon coverage is > 30x
# 2) intersect the run's vcf file with that subset bed file to get all of the variants that have amplicon cov > 30x
# 3) remove the duplicate and multi-allelic entries in the vcf file
# 4) Run annovar
# 5) Using the filtered vcf file and annovar's output, create the set of all variants, and list the status of each sample at that variant.

SOFTWARE_ROOT="/home/ionadmin/software"
SAMPLE_DIR=$1
AMP_COV_CUTOFF=$2
DEPTH_CUTOFF=$3

#cd $SAMPLE_DIR
if [ "`find ${SAMPLE_DIR}/*.vcf 2>/dev/null`" -a "`find ${SAMPLE_DIR}/*.amplicon.cov.xls 2>/dev/null`" ]
then
	# If there is are differnt vcf files from different TVC versions, then use 4.0 otherwise, use whatever's there.
	if [ "`find ${SAMPLE_DIR}/4.0*.vcf 2>/dev/null`" ]
	then
		VCF=`find ${SAMPLE_DIR}/4.0*.vcf -maxdepth 0`
	else
		VCF=`find ${SAMPLE_DIR}/*.vcf -maxdepth 0`
	fi
	AMP=`find ${SAMPLE_DIR}/*.amplicon.cov.xls -maxdepth 0`
else
	exit 4 # "file not found" error
fi

# ------------------------------------------------------------------------
# ------------ IF THERE ARE NO FILE ERRORS, START HERE -------------------
# ------------------------------------------------------------------------

TEMP_DIR="${SAMPLE_DIR}/Analysis_files"
mkdir $TEMP_DIR 2>/dev/null
#log="${TEMP_DIR}/log.txt"
log="big_log.txt"

echo >>$log
echo "--- Creating subset bed files for $SAMPLE_DIR (where amp cov > $AMP_COV_CUTOFF) ---" >>${log}
# Remove the header, and then pipe that into awk to get the amplicons with only > 30x coverage. Write it to a BED file.
tail -n +2 ${AMP} | \
	awk -v cutoff="$AMP_COV_CUTOFF" 'BEGIN{FS=OFS="\t";} {if ($10 >= cutoff) { printf("%s\t%s\t%s\t%s\t%s\n", $1, $2 - 1, $3, $4, $5); }}' \
	> ${TEMP_DIR}/sample_subset.bed
# Now intersect the subset bed file with the vcf file
bedtools intersect -a $VCF -b ${TEMP_DIR}/sample_subset.bed > ${TEMP_DIR}/intersect.vcf 2>>$log

# Remove duplicate entries, also filter multi-allelic calls
# if FAO + FRO is < Depth_Cutoff, that variant is removed
python ${SOFTWARE_ROOT}/scripts/QC/QC_Filter_Var.py ${TEMP_DIR}/intersect.vcf ${TEMP_DIR}/filtered.vcf $DEPTH_CUTOFF >> $log 2>>errors.txt
if [ "$?" != "0" ]
then
	echo "ERROR: $sample_dir had a problem filtering variants with QC_Filter_Var.py... See $log for details" >> errors.txt
	exit 1
fi

echo "--- Beginning Annovar for $SAMPLE_DIR ---" >>${log}

# First convert the vcf file so it's annovar usable
# Update in v2: using vcf4old together with snpqual 0 option. Noticed that with vcf4 format(used in v1) resulted in eliminating some of the variant calls during annotation 
/home/ionadmin/software/annovar/convert2annovar.pl \
	--format vcf4old \
	--snpqual 0
	${TEMP_DIR}/filtered.vcf \
	> ${TEMP_DIR}/annovar_input.vcf 2>>$log

# Now run Annovar to annotate the variants.
# Update in v2: use table_annovar.pl & add dbSNP, COSMIC, nonsynonymous info 
/home/ionadmin/software/annovar/table_annovar.pl \
	 ${TEMP_DIR}/annovar_input.vcf \
	 /home/ionadmin/software/annovar/humandb_ucsc/ \
	--outfile somatic.table \
	--buildver hg19 \
	--protocol refGene,snp129NonFlagged,snp137NonFlagged,cosmic68,ljb23_all  --operation g,f,f,f,f \
	-nastring . \
	--remove 
	>>$log 2>&1

