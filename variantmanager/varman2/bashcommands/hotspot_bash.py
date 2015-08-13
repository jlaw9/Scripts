import subprocess

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