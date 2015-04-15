#!/usr/bin/perl -w

# no python equivalent yet 
# jeff probably incorporated similar logic while creating data matrix though
#

use List::MoreUtils qw(firstidx);
use List::MoreUtils qw(indexes);

use strict;
use warnings;

# goal: read somatic.csv (or another genotype combination such as het_het.csv) 
# read also corresponding multianno.txt output from table_annovar.pl
# append Annovar output to the final csv result

my @splitLine=();
my $line =();

### USER INPUTS #######
my $input_csvFile=$ARGV[0]; # path to input csv file
my $transcript_file=$ARGV[1]; # path to transcripts /home/ionadmin/TRI_Scripts/Annotation/Radiogenomics_transcriptList.txt
my $annovar_File=$ARGV[2]; # path to multianno.txt from Annovar
my $output_csvFile=$ARGV[3]; # path to output csv


unless(open FILE, '>'.$output_csvFile) {
	#Die with error message
	#if we can't open it.
	die "Unable to create $output_csvFile";
}


open(my $fp, "<", $transcript_file) || die "Couldn't open '".$transcript_file."' for reading because: ".$!;

my @transcriptList=();

while(!eof $fp) {
    
    my $curr_line = readline $fp;
    chomp $curr_line;
    
    push (@transcriptList, $curr_line);
    
}

close $fp;

#print "@transcriptList\n";


open(my $fh, "<", $annovar_File) || die "Couldn't open '".$annovar_File."' for reading because: ".$!;

$line = readline $fh; # 1st line will be header

my @LineArray=<$fh>;

s{^\s+|\s+$}{}g foreach @LineArray; # get rid of trailing and leading whitespace


my @Chr_name=();
my @Chr_start=();
my @Chr_end=();
my @Variant_function=();
my @Variant_refGene=();
my @Variant_exonicFunc=();
my @Variant_snp129Flag=();
my @Variant_snp137Flag=();
my @Variant_cosmic38Flag=();
my @genomeFreq1000=();

my @SIFT_score=();
my @SIFT_prediction=();

my @PolyPhen_HIDV_score=();
my @PolyPhen_HIDV_prediction=();

my @PolyPhen_HVAR_score=();
my @PolyPhen_HVAR_prediction=();

my @Gerp_score=();
my @PhyloP_score=();
my @SiPhy_score=();


my @AAchange=();

my @AAline=();

my @temp_array=();
    
my $match_found=0;
my @test_split=();


for (my $y=0; $y<scalar @LineArray; $y++) {
    
    $match_found=0;
    
    @splitLine = split("\t",$LineArray[$y]);
    #print "---------\n";
    #print "@splitLine\n";
    
    if ($splitLine[9] ne '.' && $splitLine[9] ne 'UNKNOWN'){
        
        @AAline=split (",", $splitLine[9]);
        #print "@AAline\n";
    
        my $length=scalar @AAline;
        #print "$length\n";
        
        if ($length>1 ) {
            
    
            for (my $t=0; $t<scalar @AAline; $t++) {
        
                    @temp_array=split (":", $AAline[$t]);
                #print "$temp_array[1]\n";
                    my $index_found=firstidx {$_ eq $temp_array[1]} @transcriptList;
                #print "$index_found\n";
                
                #print "@temp_array\n";
        
                    if ($index_found>=0) {
                        
                        if (scalar @temp_array >4) {
                            
                        my @test_split=split ("p.", $temp_array[4]);
                            #print "$test_split[0]\n";
                            #print "$test_split[1]\n";
                        
                            push (@AAchange,$test_split[1]); #sometimes there is no protein change for nonframeshift indels
                        } else {
                            push (@AAchange,'.');
                        }
                        
                        $match_found=1;
                        last;

                    }
                
                
                

            }
            
            if ($match_found==0) {
                # use the last split when none of the canonical transcripts matched
                @test_split=split ("p.", $temp_array[4]);
                push (@AAchange,$test_split[1]);
            }

            
            
        } else {
            
            if ($splitLine[8] eq 'unknown'){
                
                push (@AAchange,'.');
            } else {
            
                #pair005: gene GRM1 had NM_001278064 assigned which was not among the transcript list above
            
                @temp_array=split (":", $AAline[0]);
            
                @test_split=split ("p.", $temp_array[4]);
            
                push (@AAchange,$test_split[1]);
            }
        }
        
    }elsif ($splitLine[8] eq 'unknown') {
        
        print "**** found unknown *****\n";
        print "@splitLine\n";
        
        push (@AAchange,'.');
        
    }else {
        
        push (@AAchange,'.');
        
    }
    
    
    
    push (@Chr_name, $splitLine[0]);
    push (@Chr_start, $splitLine[1]);
    push (@Chr_end, $splitLine[2]);
    push (@Variant_function,$splitLine[5]);
    push (@Variant_refGene,$splitLine[6]);
    push (@Variant_exonicFunc,$splitLine[8]);
    push (@Variant_snp129Flag,$splitLine[11]);
    push (@Variant_snp137Flag,$splitLine[12]);
    push (@Variant_cosmic38Flag,$splitLine[13]);
    push (@genomeFreq1000,$splitLine[10]);
    
    push (@SIFT_score,$splitLine[14]);
    
    if ($splitLine[16] eq "T") {
        
       push (@SIFT_prediction,"Tolerated");
        
    }elsif ($splitLine[16] eq "D") {
        
        push (@SIFT_prediction,"Deleterious");
        
    }else {
        
        push (@SIFT_prediction,$splitLine[16]);
        
    }
    
    
    
    
    push (@PolyPhen_HIDV_score,$splitLine[17]);
    
    if ($splitLine[18] eq "D") {
        
        push (@PolyPhen_HIDV_prediction,"Probably damaging");
        
    }elsif ($splitLine[18] eq "P") {
        
         push (@PolyPhen_HIDV_prediction,"Possibly damaging");
        
    }elsif ($splitLine[18] eq "B") {
        
        push (@PolyPhen_HIDV_prediction,"Benign");
    }else {
        
        push (@PolyPhen_HIDV_prediction,$splitLine[18]);
    }
    

    
    push (@PolyPhen_HVAR_score,$splitLine[19]);
    
    
    if ($splitLine[20] eq "D") {
        
        push (@PolyPhen_HVAR_prediction,"Probably damaging");
        
    }elsif ($splitLine[20] eq "P") {
        
        push (@PolyPhen_HVAR_prediction,"Possibly damaging");
        
    }elsif ($splitLine[20] eq "B") {
        
        push (@PolyPhen_HVAR_prediction,"Benign");
    }else {
        
        push (@PolyPhen_HVAR_prediction,$splitLine[18]);
    }

    
    push (@Gerp_score,$splitLine[38]);
    push (@PhyloP_score,$splitLine[39]);
    push (@SiPhy_score,$splitLine[40]);

    
    
}

#print"@Chr_name\n";
print "@Chr_start\n";
#print "@Variant_refGene\n";
print "@AAchange\n";
#print "@Variant_exonicFunc\n";

close $fh;

my $curr_chr=();
my $curr_pos=();



open(my $fg, "<", $input_csvFile) || die "Couldn't open '".$input_csvFile."' for reading because: ".$!;
    
    $line = readline $fg; # 1st line will be header

    chomp $line;

   # print the header line to output File first, and add additonal columns
#print FILE "$line\t";
    print FILE "chr\t";
    print FILE "pos\t";
    print FILE "Ref\t";
    print FILE "Alt\t";
    print FILE "Normal GT\t";
    print FILE "Normal AF\t";
    print FILE "Normal Alt depth\t";
    print FILE "Normal Ref depth\t";
    print FILE "Tumor GT\t";
    print FILE "Tumor AF\t";
    print FILE "Tumor Alt depth\t";
    print FILE "Tumor Ref depth\t";
    print FILE "Variant Function\t";
    print FILE "Variant Exonic Function\t";
    print FILE "Variant Gene\t";
    print FILE "AA change\t";
    print FILE "1000g2012apr_all\t";
    print FILE "snp129Flag\t";
    print FILE "snp137Flag\t";
    print FILE "cosmic38Flag\t";
    print FILE "LJB23_SIFT_score\t";
    print FILE "LJB23_SIFT_pred\t";
    print FILE "LJB23_Polyphen2_HDIV_score\t";
    print FILE "LJB23_Polyphen2_HDIV_pred\t";
    print FILE "LJB23_Polyphen2_HVAR_score\t";
    print FILE "LJB23_Polyphen2_HVAR_pred\t";
    print FILE "LJB23_GERP++\t";
    print FILE "LJB23_PhyloP\t";
    print FILE "LJB23_SiPhy\n";


    #print "$line\n";


my $synonymous_count=0;
my $nonsynonymous_count=0;
my $count_total=0;
my $pass_index=();

    while(!eof $fg) {
        
        my $dist_curr=10000;
        
        $line = readline $fg;
        
        chomp $line;
        
        #print "$line\n";
        
        @splitLine = split("\t",$line);
        
        
        $curr_chr=$splitLine[0];
        $curr_pos=$splitLine[1];
        
        my @index_list = indexes { $_  eq $curr_chr} @Chr_name;
        
        #print "$curr_chr\t $curr_pos\n";
       
        #print "@index_list\n";
        
        for (my $i=0; $i<scalar @index_list; $i++) {
            
           if (abs($curr_pos -$Chr_start[$index_list[$i]])< $dist_curr) {
                
               $pass_index=$index_list[$i];
               $dist_curr=abs($curr_pos -$Chr_start[$index_list[$i]]);
               #print "$pass_index\n";
               #print "$Chr_start[$pass_index]\n";
                
               #last;
            
           }
            
        }
        #print "$pass_index\n";
        #print "$Chr_start[$pass_index]\n";
        #       print "$Variant_exonicFunc[$pass_index]\n";
        
                print FILE "$line\t";
                print FILE "$Variant_function[$pass_index]\t";
                print FILE "$Variant_exonicFunc[$pass_index]\t";
        
        if ($Variant_exonicFunc[$pass_index] eq "synonymous SNV") {
            #if ($Variant_function[$pass_index] eq "exonic" & $Variant_exonicFunc[$pass_index] eq "synonymous SNV") {
            
            $synonymous_count=$synonymous_count+1;
            
            print "$Variant_exonicFunc[$pass_index]\n";
            print "$Variant_refGene[$pass_index]\n";
            
        } elsif ($Variant_exonicFunc[$pass_index] eq "nonsynonymous SNV"){
            
                $nonsynonymous_count=$nonsynonymous_count+1;
            
            print "$Variant_exonicFunc[$pass_index]\n";
            print "$Variant_refGene[$pass_index]\n";

            
        }
        
        if ($Variant_function[$pass_index] eq "exonic" | $Variant_function[$pass_index] eq "splicing") {
            
            $count_total=$count_total+1;
            
        }
                print FILE "$Variant_refGene[$pass_index]\t";
                print FILE "$AAchange[$pass_index]\t";
                print FILE "$genomeFreq1000[$pass_index]\t";
                print FILE "$Variant_snp129Flag[$pass_index]\t";
                print FILE "$Variant_snp137Flag[$pass_index]\t";
                print FILE "$Variant_cosmic38Flag[$pass_index]\t";
        
        
                print FILE "$SIFT_score[$pass_index]\t";
                print FILE "$SIFT_prediction[$pass_index]\t";
        
                print FILE "$PolyPhen_HIDV_score[$pass_index]\t";
                print FILE "$PolyPhen_HIDV_prediction[$pass_index]\t";
        
                print FILE "$PolyPhen_HVAR_score[$pass_index]\t";
                print FILE "$PolyPhen_HVAR_prediction[$pass_index]\t";
        
                print FILE "$Gerp_score[$pass_index]\t";
                print FILE "$PhyloP_score[$pass_index]\t";
                print FILE "$SiPhy_score[$pass_index]\n";

        
}


close $fg;
close FILE;

print "synonymous variant count: $synonymous_count\n";
print "non-synonymous variant count: $nonsynonymous_count\n";
print "all exonic/splicing variants: $count_total\n";

my $final_count=$count_total-$synonymous_count;


print "all exonic variants excluding synonymous: $final_count\n";



