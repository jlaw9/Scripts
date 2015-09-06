__author__ = 'matt'
import argparse
import os, sys

class Create3x3:
    def __init__(self, normal_vcf, tumor_vcf, run_depths):
        self.normal_vcf = normal_vcf
        self.tumor_vcf = tumor_vcf
        self.run_depths = run_depths

    def run(self):
        for file_path in [self.normal_vcf, self.tumor_vcf, self.run_depths]:
            if not os.path.isfile(file_path):
                print "One of the files you gave was invalid: %s" % file_path
                sys.exit()

if __name__ == '__main__':
    """
    test command on triton:
    python create_3x3.py -n /mnt/Despina/projects/PNET/A_146/QC/allA_146_Normal_Merged_11262014vsA_146_Tumor_Merged_11132014/VCF1_Final.vcf -t /mnt/Despina/projects/PNET/A_146/QC/allA_146_Normal_Merged_11262014vsA_146_Tumor_Merged_11132014/VCF2_Final.vcf -rd /mnt/Despina/projects/PNET/A_146/QC/allA_146_Normal_Merged_11262014vsA_146_Tumor_Merged_11132014/Both_Runs_depths

    """
    parser = argparse.ArgumentParser(description='VariantManager is a software suite that provides '
                                                 'several variant managing services.')

    parser.add_argument('-n','--normal_vcf', help='', required=True)
    parser.add_argument('-t','--tumor_vcf', help='', required=True)
    parser.add_argument('-rd','--run_depths', help='', required=True)

    args = parser.parse_args()

    creator = Create3x3(args.normal_vcf, args.tumor_vcf, args.run_depths)
    creator.run()