__author__ = 'matt'
import argparse
import os, sys

class Create3x3:
    def __init__(self, run_depths, matched_variants):
        self.run_depths = run_depths
        self.matched_variants = matched_variants


    def run(self):
        for file_path in [self.normal_vcf, self.tumor_vcf, self.run_depths]:
            if not os.path.isfile(file_path):
                print "One of the files you gave was invalid: %s" % file_path

        eligible_bases = self.get_eligible_bases()
        change_counts = self.get_change_counts()

    def get_eligible_bases(self):
        eligible_bases = 0
        with open(self.run_depths,'r') as infile:
            for line in infile:
                line = line.strip().split()
                line[1], line[2], line[3] = int(line[1]), int(line[2]), int(line[3])
                if line[2] >= 30 and line[3] >= 30:
                    eligible_bases += 1

        return eligible_bases

    def get_change_counts(self):
        self.change_counts = {'WT_WT':0, 'WT_HET':0, "WT_HOM":0,'HET_WT':0, 'HET_HET':0, "HET_HOM":0, \
                'HOM_WT':0, 'HOM_HET':0, "HOM_HOM":0}
        for line in self.matched_variants:
            line = line.strip().split()
            print line



if __name__ == '__main__':
    """
    test command on triton:
    python create_3x3.py -rd /mnt/Despina/projects/PNET/A_146/QC/718A_146_Normal_Merged_11262014vsA_146_Tumor_Merged_11132014/Both_Runs_depths -mv /mnt/Despina/projects/PNET/A_146/QC/718A_146_Normal_Merged_11262014vsA_146_Tumor_Merged_11132014/matched_variants.csv

    """
    parser = argparse.ArgumentParser(description='VariantManager is a software suite that provides '
                                                 'several variant managing services.')

    parser.add_argument('-rd', '--run_depths', help='', required=True)
    parser.add_argument('-mv', '--matched_variants', help='', required=True)

    args = parser.parse_args()

    creator = Create3x3(args.run_depths, args.matched_variants)
    creator.run()