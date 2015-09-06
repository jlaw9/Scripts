__author__ = 'matt'
import argparse

class Create3x3:
    def __init__(self, normal_vcf, tumor_vcf, run_depths):
        self.normal_vcf = normal_vcf
        self.tumor_vcf = tumor_vcf
        self.run_depths = run_depths

    def run(self):
        print self.normal_vcf
        print self.tumor_vcf
        print self.run_depths

if __name__ == '__main__':

    parser = argparse.ArgumentParser(description='VariantManager is a software suite that provides '
                                                 'several variant managing services.')

    parser.add_argument('-n','--normal_vcf', help='', required=True)
    parser.add_argument('-t','--tumor_vcf', help='', required=True)
    parser.add_argument('-rd','--run_depths', help='', required=True)

    args = parser.parse_args()

    creator = Create3x3(args.normal_vcf, args.tumor_vcf, args.run_depths)
    creator.run()