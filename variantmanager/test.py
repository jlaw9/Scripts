import subprocess
project_name = 'Wales'
sample = 'case2_A11'
vcf = '/rawdata/projects/Wales/case2_A11/Run1/4.2_TSVC_variants.vcf'
bam = '/rawdata/projects/Wales/case2_A11/Run1/IonXpress_011_rawlib.bam'

varman_command = "varman -p %s add SAMPLE:%s VCF:%s BAM:%s" % (project_name, sample, vcf, bam)

print 'VariantManager command executed: %s' % varman_command

child = subprocess.Popen(varman_command.split())
streamdata = child.communicate()[0]
rc = child.returncode
print 'Return Code: %s' % rc