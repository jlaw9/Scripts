from optparse import OptionParser
import xml.etree.ElementTree as ET
from Bio import SeqIO
from collections import Counter

__author__ = 'mattdyer'


#start here when the script is launched
if (__name__ == '__main__'):
    #set up the option parser
    parser = OptionParser()

    #add the options to parse
    parser.add_option('-q', '--fastq', dest='fastq', help='The FASTQ file')
    parser.add_option('-b', '--blast', dest='blast', help='The BLAST XML file')
    parser.add_option('-o', '--output', dest='output', help='The output directory')
    (options, args) = parser.parse_args()

    #parse the BLAST file
    blastRecords = ET.parse(options.blast)
    blastRoot = blastRecords.getroot()

    #import the FASTSQ file
    fastqRecords = SeqIO.parse(options.fastq, "fastq")

    #only have one FASTQ record, let's grab it and get phred qualities
    fastqRecord = fastqRecords.next()
    phredScores = fastqRecord.letter_annotations['phred_quality']

    #load the bases into an array
    bases = list(fastqRecord.seq)
    readLength = len(bases)
    deletedBases = {}

    #get the average base quality
    averagePhredScore = sum(phredScores)/len(phredScores)
    print "Read Length: %i" % (readLength)
    print "Average Base Quality (FASTQ): %s" % (averagePhredScore)

    #now we need to look at the alignments
    for hsp in blastRoot.find('BlastOutput_iterations').find('Iteration').find('Iteration_hits').find('Hit').find('Hit_hsps').findall('Hsp'):
        queryStart = int(hsp.find('Hsp_query-from').text)
        querySeq = list(hsp.find('Hsp_qseq').text)
        hitSeq = list(hsp.find('Hsp_hseq').text)
        midline = list(hsp.find('Hsp_midline').text)

        #decrement query start by 1 since coordinates in array will be 0-based
        queryStart -= 1

        #now loop over and see where we have matches, etc
        for i in range(0, len(querySeq)):
            #match
            if(midline[i] == '|'):
                bases[queryStart + i] = '*'
            else:
                #we have a mistmatch and need to figure out whether it is a mismatch, deletion, or insertion
                if(not querySeq[i] == '-' and not hitSeq[i] == '-'):
                    #mismatch
                    bases[queryStart + i] = '#'
                elif(not querySeq[i] == '-' and hitSeq[i] == '-'):
                    #insertion
                    bases[queryStart + i] = '+'
                elif(querySeq[i] == '-' and not hitSeq[i] == '-'):
                    #deletion, need to add a base to bases and phredScores
                    bases.insert(queryStart + i, '-')
                    phredScores.insert(queryStart + i, 0)
                    #offset += 1

                    #store the deleted base in the distribution
                    if(hitSeq[i] not in deletedBases):
                        deletedBases[hitSeq[i]] = 1
                    else:
                        deletedBases[hitSeq[i]] += 1


    #now let's analyze the data
    print deletedBases
    counts = Counter(bases)
    matches = counts['*']
    mismatches = counts['#']
    deletions = counts['-']
    insertions = counts['+']



    #calc what number of bases were mapped, deletion wouldn't have been in the original read
    mapped = matches + insertions + mismatches + deletions

    print "Mapped: %i (%f%%)" % (mapped, (100 * (float(mapped) / float(readLength))))
    print "Matches: %i (%f%%)" % (matches, (100 * (float(matches) / float(mapped))))
    print "Mismatches: %i (%f%%)" % (mismatches, (100 * (float(mismatches) / float(mapped))))
    print "Insertions: %i (%f%%)" % (insertions, (100 * (float(insertions) / float(mapped))))
    print "Deletions: %i (%f%%)" % (deletions, (100 * (float(deletions) / float(mapped))))

    #now let's write some circos data

    #print karyotype file, histogram, and base quality file
    karyotype = open(options.output + 'karyotype.txt', 'w')
    matches = open(options.output + 'matches.txt', 'w')
    mismatches = open(options.output + 'mismatches.txt', 'w')
    deletions = open(options.output + 'deletions.txt', 'w')
    insertions = open(options.output + 'insertions.txt', 'w')
    quality = open(options.output + 'quality.txt', 'w')
    karyotype.write('chr - r1 1 0 %i white\n' % len(bases))

    #we will use the band features to show how things mapped
    for i in range(0, len(bases)):
        quality.write('r1 %i %i %i\n' % (i, i+1, phredScores[i]))

        if(bases[i] == '*'):
            #match
            karyotype.write('band r1 0 0 %i %i green\n' % (i, i+1))
            matches.write('r1 %i %i\n' % (i, i+1))
        elif(bases[i] == '#'):
            #mismatch
            karyotype.write('band r1 0 0 %i %i red\n' % (i, i+1))
            mismatches.write('r1 %i %i\n' % (i, i+1))
        elif(bases[i] == '-'):
            #deletion
            karyotype.write('band r1 0 0 %i %i blue\n' % (i, i+1))
            deletions.write('r1 %i %i\n' % (i, i+1))
        elif(bases[i] == '+'):
            #insertion
            karyotype.write('band r1 0 0 %i %i orange\n' % (i, i+1))
            insertions.write('r1 %i %i\n' % (i, i+1))
        else:
            #not mapped
            karyotype.write('band r1 0 0 %i %i white\n' % (i, i+1))

    karyotype.close()
    matches.close()
    mismatches.close()
    insertions.close()
    deletions.close()
    quality.close()




