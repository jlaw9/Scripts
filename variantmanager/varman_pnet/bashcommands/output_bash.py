import subprocess, os

def email_file(message, attachment, address, err_out="err.log"):

    command = 'echo "%s" | (cat -; uuencode %s %s) | ' \
              'ssmtp -vvv %s' % (message, attachment, os.path.basename(attachment), address)

    with open(err_out, 'a') as err_output:
        return subprocess.call(command, stderr=err_output, shell=True)
