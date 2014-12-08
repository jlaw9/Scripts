#!/usr/bin/perl -w
#grab all the stuff from the .temp folder and remove the other garabage. Please DO NOT run this script unless you know
#what you are doing

use strict;

{
    my ($root) = @ARGV;
    print "Looking at $root\n";

    my @folders = `ls $root`;

    foreach my $folder (@folders){
	chomp($folder);
	my @subfolders = `ls $root/$folder`;
	
	foreach my $subfolder (@subfolders){
	    chomp($subfolder);
	    my $path = "$root/$folder/$subfolder/";
	    my $systemCall = "";

	    # move everything from the .temp folder if it is there
	    if( -e "$path/.temp"){		
		$systemCall = "mv $path/.temp/* $path/";
		print "$systemCall\n";
		system($systemCall);
	    }

	    # sometimes the pdf won't go so let's try it one more time
	    if(-e "$path/.temp/backupPDF.pdf"){
		$systemCall = "mv $path/.temp/backupPDF.pdf $path/";
		print "$systemCall\n";
		system($systemCall);
            }

	    # remove the .temp 
	    if(-e "$path/.temp"){
		$systemCall = "rmdir $path/.temp";
		print "$systemCall\n";
		system($systemCall);
            }

	    # remove job.sh
	    if(-e "$path/job.sh"){
		$systemCall = "rm $path/job.sh";
		print "$systemCall\n";
		system($systemCall);
            }

	    # remove bam.bai
            if(-e "$path/rawlib.bam.bai"){
                $systemCall = "rm $path/rawlib.bam.bai";
                print "$systemCall\n";
                system($systemCall);
            }

	    # remove the cov_full folder
            if(-e "$path/cov_full"){
                $systemCall = "rm -rf $path/cov_full";
                print "$systemCall\n";
                system($systemCall);
            }

	    #remove json_read
	    #if(-e "$path/cov_full"){
                $systemCall = "rm -rf $path/*.json_read";
		print "$systemCall\n";
                system($systemCall);
            #}

	    # remove xls
	    #if(-e "$path/*.xls"){
		#$systemCall = "rm $path/*.xls";
		#print "$systemCall\n";
		#system($systemCall);
            #}
	    
	    #check if the folder is empty, only has a json file, or only has json + bai
	    my @files = `ls $path/`;

	    if(scalar @files <= 1){
                $systemCall = "rm -rf $path";
                print "$path\n";
                system($systemCall);
	    }
	    
	    
	}
    }
}
