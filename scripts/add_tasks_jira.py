from jira.client import JIRA
from jira.client import GreenHopper
from optparse import OptionParser
import time

__author__ = 'mattdyer'


#this class manages creating the individual issues that we are parsing from a file
class IssueManager:

    ## The constructor
    # @param self The object pointer
    # @param jiraURL The url of the JIRA instance
    # @param jiraUser The user name to use
    # @param jiraPassword The user password to use
    def __init__(self, jiraURL, jiraUser, jiraPassword):
        self.__jiraUser = jiraUser
        self.__jiraPassword = jiraPassword
        self.__jiraURL = jiraURL
        self.startSession()

    ## Create the connection
    # @param self Teh object pointer
    def startSession(self):
        #now make the connection
        options = {
            'server':self.__jiraURL,
            'verify':False
        }
        self.__jira = JIRA(options, basic_auth=(self.__jiraUser, self.__jiraPassword))
        self.__greenhopper = GreenHopper(options, basic_auth=(self.__jiraUser, self.__jiraPassword))

    ## Kill the jira connection
    # @param self The object pointer
    def killSession(self):
        self.__jira.kill_session()
        self.__greenhopper.kill_session()

    ## Add the epic link to an issue
    # @param self The object pointer
    # @param issue The issue ID
    # @param epic The epic ID
    def attachEpic(self, issue, epic):
        #attach the epic
        self.__greenhopper.add_issues_to_epic(epic, [issue])

    ## Create an issue set by calling the createIssue and createSubtask methods
    # @param self The object pointer
    # @param project The project to add the issue to
    # @param name The summary of the issue
    # @param priority The priority of the issue
    # @param product The software product the requirement belongs to (e.g. Device, Apollo, Cloud)
    # @param components The components to add to the issues
    # @returns A dictionary of issues that were created
    def createIssueSet(self, project, name, priority, product, components):
        #dictionary to store jira issues
        issues = {}

        #set up the description
        description = '<h3>User Experience</h3><h3>Acceptance Criteria</h3><ul><li></li></ul>'

        #if we list more than one product that set the product flag to multiple
        productLabel = product

        if(';' in product):
             productLabel = 'Multiple'

        #create the parent issue
        parentID = self.createIssue(project, name, description, 'Story', priority, productLabel, components)
        issues[parentID] = '%s\t%s\t%s' % (parentID, 'Story', name)

        #create the tasks for development and testing depending on the product
        for specificProduct in product.split(';'):
            issue1 = self.createIssue(project, 'Implementation (%s): %s' % (specificProduct, name), '', 'Implement', priority, productLabel, components)
            issues[issue1] = '%s\t%s\t%s' % (issue1, 'Implement', name)
            issue2 = self.createIssue(project, 'Create Unit Tests (%s): %s' % (specificProduct, name), '', 'Unit Test', priority, productLabel, components)
            issues[issue2] = '%s\t%s\t%s' % (issue2, 'Unit Test', name)
            issue3 = self.createIssue(project, 'Verification (%s): %s' % (specificProduct, name), '', 'Verification Test', priority, productLabel, components)
            issues[issue3] = '%s\t%s\t%s' % (issue3, 'Verification Test', name)

            #create the links
            self.linkIssues(parentID, issue1, 'Develop')
            self.linkIssues(parentID, issue2, 'Verify')
            self.linkIssues(parentID, issue3, 'Verify')

        #print the ids
        return(parentID, issues)

    ## Create a new issue
    # @param self The object pointer
    # @param project The project to add the issue to
    # @param summary The summary of the issue
    # @param description The description of the issue
    # @param issueType The type of the issue
    # @param priority The priority of the issue
    # @param product The software product the requirement belongs to (e.g. Device, Apollo, Cloud)
    # @param components The components to add to the issue
    # @returns The JIRA issue identifier
    def createIssue(self, project, summary, description, issueType, priority, product, components):
        #create an issue by setting up the dictionary
        issueDict = {
            'project': {'key':project},
            'priority' : {'name':priority},
            'summary': summary,
            'description': description,
            'issuetype' : {'name':issueType},
            'labels':[
                   'AddedViaAPI'
            ],
            'customfield_11100': {'value':product}
        }

        #add the components if there are any
        if(not components == ''):
            issueDict['components'] = self.addComponents(components)

        #now create the issue
        print issueDict
        newIssue = self.__jira.create_issue(fields=issueDict)

        #return the id
        return(newIssue.key)

    ## Create a new epic
    # @param self The object pointer
    # @param project The project to add the issue to
    # @param summary The summary of the issue
    # @param description The description of the issue
    # @param issueType The type of the issue
    # @param priority The priority of the issue
    # @param product The software product the requirement belongs to (e.g. Device, Apollo, Cloud)
    # @param components The components to add to the issue
    # @returns The JIRA issue identifier
    def createEpic(self, project, summary, description, issueType, priority, product, components):
        #create an issue by setting up the dictionary
        issueDict = {
            'project': {'key':project},
            'priority' : {'name':priority},
            'summary': summary,
            'description': description,
            'issuetype' : {'name':issueType},
            'labels':[
                   'AddedViaAPI'
            ],
            'customfield_11100': {'value':product},
            'customfield_10401': summary
        }

        #add the components if there are any
        if(not components == ''):
            issueDict['components'] = self.addComponents(components)

        #now create the issue
        print issueDict
        newIssue = self.__greenhopper.create_issue(fields=issueDict)

        #return the id
        return(newIssue.key)

    ## Create a subtask issue
    # @param self The object pointer
    # @param project The project to add the issue to
    # @param summary The summary of the issue
    # @param description The description of the issue
    # @param issueType The type of the issue
    # @param priority The priority of the issue
    # @param product The software product the requirement belongs to (e.g. Device, Apollo, Cloud)
    # @param components The components to add to the task
    # @returns The JIRA issue identifier
    def createSubtask(self, project, parentID, summary, description, issueType, priority, product, components):
        #create an issue by setting up the dictionary
        issueDict = {
            'parent':{'id':parentID},
            'project': {'key':project},
            'priority' : {'name':priority},
            'summary': summary,
            'description': description,
            'issuetype' : {'name':issueType},
            'labels':[
                   'AddedViaAPI'
            ],
            'customfield_11100': {'value':product}
        }

        #add the components if there are any
        if(not components == ''):
            issueDict['components'] = self.addComponents(components)

        #now create the issue
        print issueDict
        newIssue = self.__jira.create_issue(fields=issueDict)

        #return the id
        return(newIssue.key)

    ## Link two issues
    # @param self The object pointer
    # @param jiraID1 The JIRA id of the first issue
    # @param jiraID2 The JIRA id of the second issue
    # @param linkType The type of connect
    def linkIssues(self, jiraID1, jiraID2, linkType):
        #now link the two issues
        print "Linking %s and %s" % (jiraID1, jiraID2)
        self.__jira.create_issue_link(type=linkType, inwardIssue=jiraID2, outwardIssue=jiraID1)

    ## Create an array from a ";"-separated list, used for populating components
    # @param self The object pointer
    # @param componentString The string to be parsed
    # @returns The array of components
    def addComponents(self, componentString):
        tokens = componentString.split(';')
        components = []

        #populate the array
        for token in tokens:
            components.append( {'name':token} )

        return(components)


#start here when the script is launched
if (__name__ == '__main__'):
    #set up the option parser
    parser = OptionParser()

    #add the options to parse
    parser.add_option('-u', '--user', dest='user', help='The JIRA user')
    parser.add_option('-e', '--epics', dest='epics', help='The TAB epics file (id, epic)')
    parser.add_option('-p', '--password', dest='password', help='The JIRA user password')
    parser.add_option('-s', '--site', dest='site', help='The JIRA site URL including the https:// part')
    parser.add_option('-r', '--reqs', dest='requirements', help='The TAB requirements file (id, name, priority)')
    parser.add_option('-t', '--stories', dest='stories', help='The TAB user stories file (requirements id, name, product, priority)')
    parser.add_option('-x', '--project', dest='project', help='The JIRA project')
    parser.add_option('-o', '--output', dest='output', help='The output file')
    (options, args) = parser.parse_args()

    #set up the issue manager
    manager = IssueManager(options.site, options.user, options.password)

    #load up the requirements file
    file = open(options.requirements, 'r')
    output = open(options.output, 'w')

    #create the master requirements and store the ids for mapping to user stories later
    requirementsMap = {}

    #loop over the file and create the requirements
    for line in file.readlines():
        #remove the return
        line = line.rstrip('\n')

        #tokenize the line
        tokens = line.split('\t')
        requirementID = tokens[0]
        name = tokens[1]
        priority = tokens[2]

        #now create the requirement issue and capture the id
        issueID = manager.createIssue(options.project, name, '<h3>Description</h3><h3>Market Relevance</h3>', 'Requirement', priority, 'Multiple','')
        output.write("%s\t%s\t%s\n" %(issueID, 'Requirement', name))

        #store this in the map
        requirementsMap[requirementID] = issueID

    #close the file
    file.close()

    #now load the epics
    epicsMap = {}
    file = open(options.epics, 'r')

    #loop over the file and create the requirements
    for line in file.readlines():
        #remove the return
        line = line.rstrip('\n')

        #tokenize the line
        tokens = line.split('\t')
        epicID = tokens[0]
        name = tokens[1]
        priority = tokens[2]

        #now create the requirement issue and capture the id
        issueID = manager.createEpic(options.project, 'Epic: %s' % (name), '<h3>Description</h3>', 'Epic', priority, 'Multiple','')
        output.write("%s\t%s\t%s\n" %(issueID, 'Epic', name))

        #store this in the map
        epicsMap[epicID] = issueID

    #close the file
    file.close()

    #now load the user story file and process
    file = open(options.stories, 'r')

    #loop over the file and process the user stories
    for line in file.readlines():
        #remove the return
        line = line.rstrip('\n')

        #tokenize the line
        tokens = line.split('\t')
        requirementID = tokens[0]
        epicID = tokens[1]
        name = tokens[2]
        product = tokens[3]
        priority = tokens[4]
        components = tokens[5]

        #create the issue and implement / test tasks
        issueID, issues = manager.createIssueSet(options.project, name, priority, product, components)

        for issue in issues:
            output.write('%s\n' % (issues[issue]))

        #link to the requirement / epic
        manager.linkIssues(issueID, requirementsMap[requirementID], 'Requirement')
        manager.attachEpic(issueID, epicsMap[epicID])

    #close the output file handle
    output.close()

    #kill the connection
    manager.killSession()




