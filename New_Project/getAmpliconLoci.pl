#!/usr/bin/perl -w

use strict;

my $total_pool_no=12;

my $bedFile = $ARGV[0]; #"/Users/ozlemyilmaz/Desktop/LifeTech/LifeTechKits/AmpliSeqExome_Oct2013/AmpliSeqExome.20131001.designed.bed";
my $loci=$ARGV[1]; # which position are we interested in? if 10th, then enter 10
my $startORstop=$ARGV[2]; # enter 0 for start, 1 for end-point

open(my $fg, "<", $bedFile) || die "Couldn't open '".$bedFile."' for reading because: ".$!;

my $line = readline $fg; # 1st line will be header

#my $AmpliconID=();

my $count_index=0;

while(!eof $fg) {
    
    my $line = readline $fg;
    
    chomp $line;
    
    
    my @splitLine = split("\t",$line);
    
    if ($startORstop ==0) {
        
        print "$splitLine[0]\t";
        
        my $start_pos=$splitLine[1]+$loci-1; #start position in BED-file is zero-based index, subtract -1 to account for that
        my $end_pos=$splitLine[1]+$loci+1-1; #subtract -1 again to account for end-point
        
        print "$start_pos\t";
        print "$end_pos\n";
        
    } elsif ($startORstop ==1) {
        
        print "$splitLine[0]\t";
        
        my $start_pos=$splitLine[2]-$loci;
        my $end_pos=$splitLine[2]-$loci+1;
        
        print "$start_pos\t";
        print "$end_pos\n";
        
    }
    
    
}

close $fg;


