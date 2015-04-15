#!/usr/bin/perl -w

use strict;
use warnings;

my $line=();
my @splitLine=();


my $input_csvFile=$ARGV[0]; # path to input csv file

open(my $fg, "<", $input_csvFile) || die "Couldn't open '".$input_csvFile."' for reading because: ".$!;

$line = readline $fg; # 1st line will be header

chomp $line;

print "$line\n";

while(!eof $fg) {
    
$line = readline $fg;

@splitLine = split("\t",$line);


if ($splitLine[17] eq '.') {
    
    #no dbsnp entry in 129 database
    
	#if ($splitLine[12] ne 'intronic') {
	if ($splitLine[12] eq 'exonic' || $splitLine[12] eq 'splicing') { 
        # now check if this is synonymous
        
        #print $splitLine[9];
        
		#if ($splitLine[13] ne 'synonymous SNV') {
    
            print $line;
			#}
    
    }
    
}
    
}



    


