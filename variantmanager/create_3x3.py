__author__ = 'matt'
import argparse
import os, sys

class Create3x3:
    def __init__(self, run_depths, matched_variants):
        self.run_depths = run_depths
        self.matched_variants = matched_variants


    def run(self):
        for file_path in [self.run_depths, self.matched_variants]:
            if not os.path.isfile(file_path):
                print "One of the files you gave was invalid: %s" % file_path

        run_title = "all: " + os.path.abspath(self.run_depths).split("/")[-2].split('vs')[0][3:] + \
                    " - vs - " + os.path.abspath(self.run_depths).split("/")[-2].split('vs')[1]

        eligible_bases = self.get_eligible_bases()
        three_by_three = self.generate_three_by_three(eligible_bases)

        print run_title
        print "error rate: %s" % three_by_three['error_rate']
        print "% available bases: null"
        print "# of GTs reassigned: null"
        print "\tWT\tHET\tHOM\tSum:"
        print "WT\t%d\t%d\t%d\t%d" % (three_by_three['WT_WT'], three_by_three['WT_HET'], three_by_three['WT_HOM'],
                                     sum([three_by_three['WT_WT'], three_by_three['WT_HET'], three_by_three['WT_HOM']]))
        print "HET\t%d\t%d\t%d\t%d" % (three_by_three['HET_WT'], three_by_three['HET_HET'], three_by_three['HET_HOM'],
                                     sum([three_by_three['HET_WT'], three_by_three['HET_HET'], three_by_three['HET_HOM']]))
        print "HOM\t%d\t%d\t%d\t%d" % (three_by_three['HOM_WT'], three_by_three['HOM_HET'], three_by_three['HOM_HOM'],
                                     sum([three_by_three['HOM_WT'], three_by_three['HOM_HET'], three_by_three['HOM_HOM']]))
        print "Sum:\t%d\t%d\t%d\t%d" % (sum([three_by_three['WT_WT'], three_by_three['HET_WT'], three_by_three['HOM_WT']]),
                                        sum([three_by_three['WT_HET'], three_by_three['HET_HET'], three_by_three['HOM_HET']]),
                                        sum([three_by_three['WT_HOM'], three_by_three['HET_HOM'], three_by_three['HOM_HOM']]),
                                        three_by_three['total_eligible_bases'])
        print


    def get_eligible_bases(self):
        eligible_bases = 0
        with open(self.run_depths,'r') as infile:
            for line in infile:
                line = line.strip().split()
                line[1], line[2], line[3] = int(line[1]), int(line[2]), int(line[3])
                if line[2] >= 30 and line[3] >= 30:
                    eligible_bases += 1

        return eligible_bases

    def generate_three_by_three(self, eligible_bases):
        change_counts = {'WT_WT':0, 'WT_HET':0, "WT_HOM":0,'HET_WT':0, 'HET_HET':0, "HET_HOM":0, \
                'HOM_WT':0, 'HOM_HET':0, "HOM_HOM":0}
        with open(self.matched_variants, 'r') as infile:
            header = infile.readline().strip().split("\t")
            header = [val.strip() for val in header]

            for line in infile:
                var = {header[i]: line.strip().split()[i] for i in range(len(line.strip().split()))}
                if var['Run1 GT'] == 'WT' and var['Run2 GT'] == 'WT':
                    change_counts['WT_WT'] += 1
                elif var['Run1 GT'] == 'WT' and var['Run2 GT'] == 'HET':
                    change_counts['WT_HET'] += 1
                elif var['Run1 GT'] == 'WT' and var['Run2 GT'] == 'HOM':
                    change_counts['WT_HOM'] += 1
                elif var['Run1 GT'] == 'HET' and var['Run2 GT'] == 'WT':
                    change_counts['HET_WT'] += 1
                elif var['Run1 GT'] == 'HET' and var['Run2 GT'] == 'HET':
                    change_counts['HET_HET'] += 1
                elif var['Run1 GT'] == 'HET' and var['Run2 GT'] == 'HOM':
                    change_counts['HET_HOM'] += 1
                elif var['Run1 GT'] == 'HOM' and var['Run2 GT'] == 'WT':
                    change_counts['HOM_WT'] += 1
                elif var['Run1 GT'] == 'HOM' and var['Run2 GT'] == 'HET':
                    change_counts['HOM_HET'] += 1
                elif var['Run1 GT'] == 'HOM' and var['Run2 GT'] == 'HOM':
                    change_counts['HOM_HOM'] += 1

            change_counts['WT_WT'] = (eligible_bases - sum(change_counts.values())) + change_counts['WT_WT']
            change_counts['error_count'] = change_counts['HET_WT'] + change_counts['HOM_WT'] + change_counts['HOM_HET']
            change_counts['error_rate'] = float(change_counts['error_count']) / float(eligible_bases)
            change_counts['total_eligible_bases'] = eligible_bases

            return change_counts



if __name__ == '__main__':
    """
    test command on triton:
    python2.7 create_3x3.py -rd /mnt/Despina/projects/PNET/A_146/QC/allA_146_Normal_Merged_11262014vsA_146_Tumor_Merged_11132014/Both_Runs_depths -mv /mnt/Despina/projects/PNET/A_146/QC/allA_146_Normal_Merged_11262014vsA_146_Tumor_Merged_11132014/matched_variants.csv

    """
    parser = argparse.ArgumentParser(description='VariantManager is a software suite that provides '
                                                 'several variant managing services.')

    parser.add_argument('-rd', '--run_depths', help='', required=True)
    parser.add_argument('-mv', '--matched_variants', help='', required=True)

    args = parser.parse_args()

    creator = Create3x3(args.run_depths, args.matched_variants)
    creator.run()