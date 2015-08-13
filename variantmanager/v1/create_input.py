# -----------------------------------------------------------
# ----------- FUNCTIONS DEFINED HERE ------------------------
# -----------------------------------------------------------

import json
import sys
import os
import fnmatch
import glob

class CreateInput:

    def __init__(self, project_dir):
        self.project_dir = project_dir

    def main(self):
        json_files = self.getJsonFiles(self.project_dir)

        print "\t".join(["ID", "VCF", "BAM"])
        for file in json_files:

            jsonData = json.load(open(file))

            try:
                if "json_type" in jsonData and jsonData["json_type"] == "sample":
                    final_dir = os.path.dirname(jsonData['final_json'])
                    sample_id = final_dir.split("/")[-2]
                    final_vcf = glob.glob(final_dir+"/*.vcf")[0]
                    final_bams = glob.glob(final_dir+"/*.bam")

                    for bam in final_bams:
                        if "Merged" in os.path.basename(bam):
                            final_bam = bam
                            break
                        elif "IonXpress" in bam:
                            final_bam = bam

                    print "\t".join([sample_id, final_vcf, final_bam])

            except KeyError:
                continue

        sys.exit()

    # @param project_dir the dir in which to find the json files used to find the vcf files to pool the variants
    # @param hotspot the output hotspot file
    def getJsonFiles(self, project_dir):
        json_files = []
        for root, dirnames, filenames in os.walk(project_dir):
            for filename in fnmatch.filter(filenames, "*.json"):
                json_files.append(os.path.join(root, filename))

        return json_files


if __name__ == '__main__':
    project_dir = sys.argv[1]
    creator = CreateInput(project_dir)

    creator.main()