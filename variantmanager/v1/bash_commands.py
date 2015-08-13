import os
import subprocess



# -----------------------------------------------------------
# ----------- FUNCTIONS DEFINED HERE ------------------------
# -----------------------------------------------------------


class BashCommands:

    @staticmethod
    def remove_tmp_dir(project_analysis_path, logger=None):
        tmp_path = project_analysis_path + "/.tmp"

        if os.path.isdir(tmp_path):
            if logger: logger.info('Removing Tmp Folder: ' + tmp_path)
            return subprocess.call(("rm -r " + tmp_path).split())

    @staticmethod
    def make_tmp_dir(project_analysis_path, logger=None):
        tmp_path = project_analysis_path + "/.tmp"

        if not os.path.isdir(tmp_path):
            if logger: logger.info('Making Tmp Folder: ' + tmp_path)
            subprocess.call(("mkdir " + tmp_path).split())
            return tmp_path

    @staticmethod
    def make_dir(directory, logger=None):
        if not os.path.isdir(directory):
            return subprocess.call(("mkdir " + directory).split())

    @staticmethod
    def remove_dir(directory, logger=None):
        if os.path.isdir(directory):
            return subprocess.call(("rm -r " + directory).split())

    @staticmethod
    def make_file(file):
        if not os.path.isfile(file):
            with open(file, "w"):
                pass

    @staticmethod
    def remove_file(file):
        if os.path.isfile(file):
            return subprocess.call(("rm " + file).split())

    @staticmethod
    def rename_file(file_name, new_name):
        if os.path.isfile(file_name):
            return subprocess.call(("mv %s %s" % (file_name, new_name)).split())

    @staticmethod
    def copy_file(orig_path, copy_path, logger=None):
        command = ("cp %s %s") % (orig_path, copy_path)
        return subprocess.call(command.split())

    @staticmethod
    def bgzip(file_path, logger=None):
        command = "bgzip " + file_path
        return subprocess.call(command.split())

    @staticmethod
    def tabix(file_path, logger=None):
        new_file = file_path + ".gz"
        command = "tabix -p vcf " + new_file
        subprocess.call(command.split())
        return new_file

    @staticmethod
    def annotate_annovar(vcf_path, out_file, err_out="err.log"):

        command = 'annovar/table_annovar.pl %s /rawdata/software/annovar/humandb_ucsc/ ' \
                  '-outfile %s ' \
                  '-buildver hg19 ' \
                  '-protocol refGene,1000g2012apr_all,snp137NonFlagged,cosmic68,ljb23_all ' \
                  '-operation g,f,f,f,f ' \
                  '-remove ' \
                  '-otherinfo ' \
                  '-nastring . ' \
                  '-vcfinput' % (vcf_path, out_file)

        with open(err_out, 'a') as err_output:
            return subprocess.call(command.split(), stderr=err_output)

    @staticmethod
    def cat_csv_with_header(header, all_files, file_name, err_out="err.log"):
        if isinstance(header, list):
            header = ",".join(header)

        command = '(echo "%s"; cat %s) > %s' % (header, " ".join(all_files), file_name)

        with open(err_out, 'a') as err_output:
            return subprocess.call(command, shell=True, stderr=err_output)

    @staticmethod
    def cat_vcf_with_header(header, all_files, file_name, err_out="err.log"):
        if isinstance(header, list):
            header = "\t".join(header)

        command = '(echo "%s"; cat %s) > %s' % (header, " ".join(all_files), file_name)

        with open(err_out, 'a') as err_output:
            subprocess.call(command, shell=True, stderr=err_output)

    @staticmethod
    def tvc_hotspot(tvc_hotspot, output_dir, output_vcf, ref_fasta, bam_file, bed_file, tvc_json, err_out="err.log"):

        command = 'tvc --output-dir %s ' \
                  '--output-vcf %s ' \
                  '--reference %s ' \
                  '--input-bam %s ' \
                  '--target-file %s ' \
                  '--trim-ampliseq-primers ' \
                  '--target-file %s ' \
                  '--input-vcf %s ' \
                  '--process-input-positions-only ' \
                  '--use-input-allele-only ' \
                  '--parameters-file %s' % (output_dir, output_vcf, ref_fasta, bam_file,
                                            bed_file, bed_file, tvc_hotspot, tvc_json)


        with open(err_out, 'a') as err_output:
            return subprocess.call(command.split(), stderr=err_output)

    @staticmethod
    def prep_hotspot(hotspot_in, hotspot_out, ref_fasta, err_out="err.log"):

        command = 'tvcutils ' \
                  'prepare_hotspots ' \
                  '-v %s ' \
                  '-o %s ' \
                  '-r %s ' \
                  '-s on ' \
                  '-a on' % (hotspot_in, hotspot_out, ref_fasta)

        with open(err_out, 'a') as err_output:
            return subprocess.call(command.split(), stderr=err_output)

