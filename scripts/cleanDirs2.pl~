#!/usr/bin/perl -w

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
	    my $systemCall = "python cleanRunDir.py -f $path";
	    #print "$systemCall\n";
	    system($systemCall);
	}
    }
}
