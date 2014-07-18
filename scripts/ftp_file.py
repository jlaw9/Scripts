from ftplib
from optparse import OptionParser

__author__ = 'mattdyer'


#start here when the script is launched
if (__name__ == '__main__'):
    #set up the option parser
    parser = OptionParser()

    #add the options to parse
    parser.add_option('-u', '--user', dest='network', help='User name')
    parser.add_option('-p', '--password', dest='password', help='Password')
    parser.add_option('-s', '--server', dest='server', help='Server')
    parser.add_option('-f', '--file', dest='file', help='File')
    parser.add_option('-l', '--location', dest='location', help='Location')
    (options, args) = parser.parse_args()

    #connect to ftp site
    ftp = FTP(host=options.server)
    ftp.login(user=options.user, passwd=options.password)

    print ftp.getwelcome()

    #make the directory
    ftp.mkd(options.location)

    #push the file
    ftp.push

    #close the connection
    ftp.quit()