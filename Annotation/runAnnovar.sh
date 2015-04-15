#example: ./runAnnovar.sh ~/ozlem/lam/H4/N-1vsT-7/annovar_out/

cd $1 # argument 1 is the file dir where output from getAnnovarInputFiles.sh can be found

#create input files compatible with annovar 
/home/ionadmin/software/annovar/convert2annovar.pl --format vcf4old --snpqual 0 somatic.vcf > somatic_input.vcf
/home/ionadmin/software/annovar/convert2annovar.pl --format vcf4old --snpqual 0 loh.vcf > loh_input.vcf
/home/ionadmin/software/annovar/convert2annovar.pl --format vcf4old --snpqual 0 het_het.vcf > het_het_input.vcf
/home/ionadmin/software/annovar/convert2annovar.pl --format vcf4old --snpqual 0 hom_hom.vcf > hom_hom_input.vcf
/home/ionadmin/software/annovar/convert2annovar.pl --format vcf4old --snpqual 0 het_wt.vcf > het_wt_input.vcf

# run annovar  


/home/ionadmin/software/annovar/table_annovar.pl somatic_input.vcf \
	 /home/ionadmin/software/annovar/humandb_ucsc/ --outfile annovar_somatic_table \
	 --buildver hg19 --protocol refGene,1000g2012apr_all,snp129NonFlagged,snp137NonFlagged,cosmic68,ljb23_all \
	 --operation g,f,f,f,f,f --remove --nastring . 


/home/ionadmin/software/annovar/table_annovar.pl loh_input.vcf \
	     /home/ionadmin/software/annovar/humandb_ucsc/ --outfile annovar_loh_table \
		      --buildver hg19 --protocol refGene,1000g2012apr_all,snp129NonFlagged,snp137NonFlagged,cosmic68,ljb23_all \
			       --operation g,f,f,f,f,f --remove --nastring . 

/home/ionadmin/software/annovar/table_annovar.pl het_het_input.vcf \
	     /home/ionadmin/software/annovar/humandb_ucsc/ --outfile annovar_het_het_table \
		      --buildver hg19 --protocol refGene,1000g2012apr_all,snp129NonFlagged,snp137NonFlagged,cosmic68,ljb23_all \
			       --operation g,f,f,f,f,f --remove --nastring . 

/home/ionadmin/software/annovar/table_annovar.pl hom_hom_input.vcf \
	     /home/ionadmin/software/annovar/humandb_ucsc/ --outfile annovar_hom_hom_table \
		      --buildver hg19 --protocol refGene,1000g2012apr_all,snp129NonFlagged,snp137NonFlagged,cosmic68,ljb23_all \
			       --operation g,f,f,f,f,f --remove --nastring . 

/home/ionadmin/software/annovar/table_annovar.pl het_wt_input.vcf \
	     /home/ionadmin/software/annovar/humandb_ucsc/ --outfile annovar_het_wt_table \
		      --buildver hg19 --protocol refGene,1000g2012apr_all,snp129NonFlagged,snp137NonFlagged,cosmic68,ljb23_all \
			       --operation g,f,f,f,f,f --remove --nastring . 




