#! /usr/bin/env python2.7
__author__ = 'durrantmm'

from bash_commands import BashCommands

class Plink:
    def __init__(self, project_config, mongodb, logger):
        self.project_config = project_config
        self.project_name = self.project_config['project_name']
        self.mongodb = mongodb
        self.logger = logger

    def run(self):
        self.logger.info("Beginning Plink Analysis")
        self.make_plink_files()


    def make_plink_files(self):

        self.make_map_file()
        self.make_ped_file()
        self.logger.info('Finished making plink files')

    def make_map_file(self):
        self.mongodb.open_connection()
        self.logger.info("Making MAP file")

        plink_path = self.project_config['output_dir'] + "/plink"
        BashCommands.make_dir(plink_path)

        mapfile_path = plink_path + "/" + self.project_name + ".map"

        with open(mapfile_path, "w") as out_file:

            annotations = self.mongodb.get_var_annotations()

            var_list = []
            last_var_id = "0|0|0"

            for annot in annotations:

                chrom, pos, id, ref, alt = annot['CHROM'], annot['POS'], annot['ANNOVAR']['snp137NonFlagged'], \
                                           annot['REF'], annot['ALT']
                if id == ".":
                    id = "%s_%s" % (chrom, pos)

                var_id = "|".join([str(chrom), str(pos)])
                list_entry = [str(chrom), str(id), 0, str(pos), str(ref), str(alt)]

                if var_id != last_var_id:

                    if len(var_list) == 1:
                        map_var = var_list[0]
                        out_file.write("\t".join([str(val) for val in map_var[:4]]) + "\n")
                        map_var_dict_keys = ['CHROM', 'ID', 'GD', 'POS', 'REF', 'ALT']
                        map_var_dict = {map_var_dict_keys[i]: map_var[i] if map_var_dict_keys[i] in ["ID", "REF", "ALT"]
                                        else int(map_var[i]) for i in range(len(map_var))}
                        map_var_dict.update({"TYPE": "MAP"})

                        self.mongodb.add_plink_doc(map_var_dict, self.project_name)

                    del var_list[:]
                    var_list = []

                    var_list.append(list_entry)
                    last_var_id = var_id

                else:
                    var_list.append(list_entry)

        self.logger.debug("Creating index for plink collection")
        self.mongodb.create_plink_index()
        self.mongodb.close_connection()

    def make_ped_file(self):
        self.logger.info("Making PED file")

        plink_path = self.project_config['output_dir'] + "/plink"
        ped_path = plink_path + "/" + self.project_name + ".ped"

        self.mongodb.open_connection()



        sample_names = self.mongodb.get_sample_names(self.project_name)

        ped_file = open(ped_path, 'w')

        for sample in sample_names:

            samplevar_batch = self.mongodb.load_sample_variants(self.project_name, sample)

            sample_header = " ".join([str(val) for val in [sample, sample, 0, 0, 0]]) + "\t-9\t"

            ped_file.write(sample_header)

            plink_variants = self.mongodb.get_plink_variants(self.project_name)
            for var in plink_variants:

                var_key = "|".join([str(var['CHROM']), str(var['POS'])])

                if var_key in samplevar_batch:

                    sample_var = samplevar_batch[var_key]
                    if sample_var['TOTAL_READS'] < 30:
                        ped_file.write('   %d %d' % (0, 0))

                    elif sample_var['PASS/FAIL'] == 'FAIL':
                        ped_file.write('   %d %d' % (0, 0))
                    else:
                        allele1 = int(sample_var['GT'].split('/')[0])
                        allele2 = int(sample_var['GT'].split('/')[1])

                        alleles = [sample_var['REF']] + sample_var['ALT']

                        ped_file.write('   %s %s' % (alleles[allele1], alleles[allele2]))

                else:
                    ped_file.write('   %s %s' % (var['REF'], var['REF']))



            ped_file.write('\n')

        ped_file.close()





