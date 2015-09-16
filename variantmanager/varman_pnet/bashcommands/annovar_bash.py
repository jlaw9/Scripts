import subprocess
from glob import glob

def annotate_annovar(vcf_path, out_file, err_out="err.log"):

    command = 'varman2/annovar/table_annovar.pl %s /rawdata/software/annovar/humandb_ucsc/ ' \
              '-outfile %s ' \
              '-buildver hg19 ' \
              '-protocol refGene,1000g2012apr_all,snp137NonFlagged,cosmic68,ljb23_all ' \
              '-operation g,f,f,f,f ' \
              '-remove ' \
              '-otherinfo ' \
              '-nastring . ' \
              '-vcfinput' % (vcf_path, out_file)

    with open(err_out, 'a') as err_output:
        subprocess.call(command.split(), stderr=err_output)

    anno_file = glob(out_file+"*multianno*")[0]

    return anno_file