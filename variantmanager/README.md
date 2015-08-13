# README #
Welcome to VariantManager! A comprehensive system for managing and analyzing next generation sequencing data sets.

*****
### Basic Functions ###
* Loads your original VCF files into a MongoDB database.
* Annotates all of your variants by annovar.
* Calculates variant statistics in regards to read number(Using TOST and t-test analysis) to determine some potentially erroneous variant calls.
* Hotspots all of the variants to determine nocalls and wild type calls, also accounts for previous statistical analyses.
* The previous step allows for the identification of high-quality rare variants (frequency < 0.05 in population), which can then be analyzed in the context of the gene or genomic region as a whole.
* Writes all the variants to plink format and executes some basic plink analyses.

* [Learn Markdown](https://bitbucket.org/tutorials/markdowndemo)

*****
### Installation ###
* Download the entire git repository.
* Run varman.py according to the necessary commandline parameters.
* Execute `./varman.py -h` for all the necessary parameters.

*****
### VariantManager Input Format ###

* VariantManager is a secondary analysis tool for your data set, but to perform these secondary analyses, including hotspotting, etc., it is necessary that the application has access to all of your original bam files.
* The input is in a column format with the following headers, in any order, seperated by white space:
	* ID - A unique identifier to be used to refer to the sample
	* BAM - the absolute path to the associated BAM file.
	* VCF - the absolute path to the associated VCF file.
	* SEX - the gender of the sample (missing = 0, male = 1, female = 2)
	* AFFECTED - the case/control status of the sample (0 = missing, 1 = unaffected/control, 2 = affected/case)

For example:

```
ID	BAM	VCF	SEX	AFFECTED
NA1010	path/to/sample.bam	path/to/sample.vcf	2	1
NA11234	path/to/sample.bam	path/to/sample.vcf	2	1
NA41223	path/to/sample.bam	path/to/sample.vcf	1	2
NA1234	path/to/sample.bam	path/to/sample.vcf	2	0
NA1125	path/to/sample.bam	path/to/sample.vcf	2	2
```

	
*****
### Who do I talk to? ###

* Matt Durrant
	* Email: durrantmm@gmail.com