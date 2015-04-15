# example: /getAnnovarInputFiles.sh /home/ionadmin/ozlem/lam/H4/N-1vsT-7/

# goal: when you QC 2 runs, you will get matched_variants.csv, VCF1_Final and VCF2_Final
# if you would like to subset out somatic, loh calls separately this is the script to use 
# this script is meant to generate the files necessary to run Annovar 

cd $1 # argument 1 is the file dir where matched_csv, VCF1_Final and VCF2_final can be found 
	  # full path should be given, see the example above


subDir=$1/annovar_out

echo $subDir

if [ ! -d $subDir ]
then 
	mkdir $subDir
fi

# create somatic.csv and loh.csv 
#together with het_het.csv and hom_hom.csv 

grep -E "WT.+HET" matched_variants.csv > $1/annovar_out/somatic.csv 

grep -E "HET.+HOM" matched_variants.csv > $1/annovar_out/loh.csv

grep -E "HET.+HET" matched_variants.csv > $1/annovar_out/het_het.csv

grep -E "HOM.+HOM" matched_variants.csv > $1/annovar_out/hom_hom.csv

#let's create het_wt.csv as well since this could be a special case (LOH) 

grep -E "HET.+WT" matched_variants.csv > $1/annovar_out/het_wt.csv


# now create the corresponding VCF

cd $1/annovar_out 

python2.7 /home/ionadmin/TRI_Scripts/Variants/getVCF_v2.py ./somatic.csv $1/VCF2_Final.vcf ./somatic_spaced.vcf
python2.7 /home/ionadmin/TRI_Scripts/Variants/getVCF_v2.py ./loh.csv $1/VCF2_Final.vcf ./loh_spaced.vcf
python2.7 /home/ionadmin/TRI_Scripts/Variants/getVCF_v2.py ./het_het.csv $1/VCF2_Final.vcf ./het_het_spaced.vcf
python2.7 /home/ionadmin/TRI_Scripts/Variants/getVCF_v2.py ./hom_hom.csv $1/VCF2_Final.vcf ./hom_hom_spaced.vcf
python2.7 /home/ionadmin/TRI_Scripts/Variants/getVCF_v2.py ./het_wt.csv $1/VCF2_Final.vcf ./het_wt_spaced.vcf


#reformat the VCF files (replace space with tab) unless you can correct the getVCF_v2.py script 

python /home/ionadmin/TRI_Scripts/Variants/reWriteVCF.py ./somatic_spaced.vcf ./somatic.vcf
python /home/ionadmin/TRI_Scripts/Variants/reWriteVCF.py ./loh_spaced.vcf ./loh.vcf
python /home/ionadmin/TRI_Scripts/Variants/reWriteVCF.py ./het_het_spaced.vcf ./het_het.vcf
python /home/ionadmin/TRI_Scripts/Variants/reWriteVCF.py ./hom_hom_spaced.vcf ./hom_hom.vcf
python /home/ionadmin/TRI_Scripts/Variants/reWriteVCF.py ./het_wt_spaced.vcf ./het_wt.vcf

# remve the wrong formatted files 

rm somatic_spaced.vcf
rm loh_spaced.vcf
rm het_het_spaced.vcf
rm hom_hom_spaced.vcf 
rm het_wt_spaced.vcf 





