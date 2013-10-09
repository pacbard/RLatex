#!/usr/bin/env python2.7

from __future__ import print_function
import sys, httplib, getopt
from xml.etree.ElementTree import Element, SubElement, Comment
from xml.etree import ElementTree
from xml.dom import minidom
import re
import logging
import os.path
import base64
import time
import urllib
import shlex

__applicationName__ = "rlatex"
__version__ = "0.8"
__date__ = "October 5th, 2013"
__website__ = "http://pacbard.github.com/RLatex"
__author__ = "Emanuele 'pacbard' Bardelli (bardellie at gmail dot com)"

__doc__ = """
A CLSI server command line client.

Usage: {0} [options] inputfile.tex

Options:

    -h, --help:         print this message
    -s, --server:       the CLSI server to contact
    -a, --api_url:      API URl on the server
    -t, --token:        your token
    -f, --file:         get login information from a file
    -c, --compiler      sets the LaTeX Compiler
    -o, --output        sets the LaTeX output file
    -l, --log:          saves the log file
    -d, --debug:        debug version of the script
    --async             compiles asynchronously

The CLSI interface supports the following compilers and outputs:
    pdflatex    pdf
    latex       dvi, pdf, ps
    xelatex     pdf
    standalone  png, jpg
"""

__licenseName__ = "GPL v3"
__license__ = """
RLatex - A CLSI server command line client.
Copyright (C) 2013  Emanuele Bardelli <bardellie@gmail.com>

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""

class FSM(object):
    """
    Implements a finite state machine.

    Transitions are given as 4-tuples, consisting of an origin state, a target
    state, a condition for the transition (given as a reference to a function
    which gets called with a given piece of input) and a pointer to a function
    to be called upon the execution of the given transition.

    \var transitions holds the transitions
    \var current_state holds the current state
    \var current_input holds the current input
    \var current_transition hold the currently active transition
    """

    def __init__(self, start_state=None, transitions=[]):
        self.transitions = transitions
        self.current_state = start_state
        self.current_input = None
        self.current_transition = None

    def setStartState(self, state):
        self.current_state = state

    def addTransition(self, from_state, to_state, condition, callback):
        self.transitions.append([from_state, to_state, condition, callback])

    def makeTransition(self, input):
        """
        Makes a transition based on the given input.

        @param input input to parse by the FSM
        """

        for transition in self.transitions:
            [from_state, to_state, condition, callback] = transition
            if from_state == self.current_state:
                match = condition(input)
                if match:
                    self.current_state = to_state
                    self.current_input = input
                    self.current_transition = transition
                    if options.debug:
                        print >>sys.stderr, "# FSM: executing (%s -> %s) for line '%s'" % (from_state, to_state, input)
                    callback(match)
                    return

class rlatex(object):
    def __init__(self):
        """
        Init function

        __init__() initializes the class variables to None or False
        """

        self.host, self.api_url, self.token, self.texsource, self.texpath = (None,) * 5
        self.log, self.debug = (False,) *2
        self.login = self.scriptPath()+'/login.txt'
        self.compiler = 'pdflatex'
        self.output = 'pdf'
        self.sync = True
        self.graphicspath = ['']
        self.graphicextensions = ['.png', '.jpg', '.pdf']

    def _debug(self, msg):
        if self.debug:
            logging.info(msg)

    def _parse(self, tex):
        a = []
        # Get content of outer {}
        c = re.search(r'\{(.+)\}', tex).group(1)
        # Split string at {
        c = re.split("{", c)
        for elem in c:
            if "\\" not in elem:
                # Delete leftover }
                elem = elem.replace("}", "")
                #  Append if string is not empty
                a += re.split(",", elem)
        return(a)

    def compile(self, argv):
        """
        Compile function

        Compile function.  This wraps the compile task
        @param argv The command line arguments passed by the user
        """

        self.manageArgv(argv)

        self.loadLogin()

        XMLrequest = self.buildRequest(self.texpath, self.texsource)
        try:
            toDownload = self.do_request(XMLrequest)
        except Exception, e:
            sys.exit("No output from the server")
        else:
            self.fetchResult(toDownload)

    def loadLogin(self):
        """
        Loads login information or asks them through command line

        This function loads the default login file.  If the login file was
        passed using the argument -f, it should just skip it.
        You can provide a filename here and the script will read your login
        information from that file. The format must be:
         * server = 'foo.com'
         * api_url = 'clsi/compile'
         * token = 'token'
        """

        try:
            with open(self.login, 'r') as f:
                self._debug('Login information found in file {0}.'.format(self.login))
                get_val = lambda x: x.split('=')[1].strip().strip('\'"')
                for line in f:
                    if not line.startswith('#'):
                        if line.startswith('server') and not self.host:
                            self.host = get_val(line)
                        if line.startswith('api_url') and not self.api_url:
                            self.api_url = get_val(line)
                        if line.startswith('token') and not self.token:
                            self.token = get_val(line)
        except IOError as e:
            print (self.login, " not found")
            self._debug(self.login + " not found")

        if not self.host:
            self.host = raw_input('Enter server: ')
        if not self.api_url:
            self.api_url = raw_input('Enter API URL: ')
        if not self.token:
            self.token = raw_input('Enter token:  ')

        # Screen confirmation of the settings
        self._debug("Server: " + self.host)
        self._debug("API URL: " + self.api_url)
        self._debug("Token: " + self.token)

    def manageArgv(self, argv):
        """
        Argument management

        Checks if all the flags are correct
        """

        try:
            opts, file = getopt.getopt(argv[1:], 'hlds:a:t:f:l:c:o:',
                                ['help', 'log', 'debug', 'async' , 'server=', 'api_url=', 'token=', 'file=', 'compiler=', 'output='])
        except getopt.GetoptError as err:
            print(str(err), __doc__ , sep='\n\n')
            sys.exit(2)

        # Exits if more than one file is passed to the script
        # @todo check if pdflatex supports more than one argument
        if len(file) != 1:
            print('Error: must specify exactly one file. Please specify options first.',__doc__, sep='\n\n')
            sys.exit(2)

        for o, a in opts:
            if o in ('-h', '--help'):
                print(usage)
                sys.exit(2)
            elif o in ('-s', '--server'):
                self.host = a
            elif o in ('-a', '--api_url'):
                self.api_url = a
            elif o in ('-t', '--token'):
                self.token = a
            elif o in ('-f', '--file'):
                self.login = a
            elif o in ('-l', '--log'):
                self.log = True
            elif o in ('-c', '--compiler'):
                self.compiler = a
            elif o in ('-o', '--output'):
                self.output = a
            elif o in ('-d', '--debug'):
                self.debug = True
            elif o in ('--async'):
                self.sync = False

        # Splits the argument in the path and the source
        self.texpath, self.texsource = os.path.split(file[0])

        if self.texpath != "":
            self.texpath += "/"

        # Gets the file name without the extension
        self.texsource = os.path.splitext(self.texsource)[0]

        # Starts the logger if debug flag is TRUE
        if self.debug:
            logging.basicConfig(filename=self.texpath+'rlatex.log',
                                filemode='w',
                                level=logging.DEBUG,
                                format='%(asctime)s\n%(message)s',
                                datefmt='%m/%d/%Y %I:%M:%S %p')

    def scriptPath(self):
        """
        Returns the script installation path

        scriptPath() returns the script path.
        If the application is compiled with py2exe, it will use the
        frozen status.
        This function is used to load the login file from the installation
        directory of the script.
        @return string The script path
        """

        if hasattr(sys, 'frozen'):
            basis = sys.executable
        else:
            basis = os.path.realpath(__file__)
        return(os.path.split(basis)[0])

    def do_request(self, xml_request):
        """
        Posts the XML request

        do_request posts the XML request to the CLSI server.
        This is based on HTTP XML Post request, by www.forceflow.be
        It returns the server response to the request.
        If the --debug flag is set, it will dump the XML request and the
        server response in the debug file.
        """

        webservice = httplib.HTTP(self.host)
        webservice.putrequest("POST", self.api_url)
        webservice.putheader("Host", self.host)
        webservice.putheader("User-Agent",__applicationName__+__version__ )
        webservice.putheader("Content-type", "text/xml; charset=\"UTF-8\"")
        webservice.putheader("Content-length", "%d" % len(xml_request))
        webservice.endheaders()
        webservice.send(xml_request)
        statuscode, statusmessage, header = webservice.getreply()
        result = webservice.getfile().read()
        id = self.getTag(result, 'compile_id')
        self._debug("XML request\n"+xml_request+"\nXML request result\n"+result)
        while self.getTag(result, 'status') == "unprocessed":
            result = self.downloadID(id)
            self._debug("Unprocessed Request found\n"+xml_request+"\nXML request result\n"+result)
        return result

    def getTag(self, xml, tag):
        tree = ElementTree.fromstring(xml)
        return tree.findtext(tag)

    def downloadID(self, id):
        '''
        Downloads the result.xml for the compile ID

        downloadID() handles the download of the result.xml file during asynchronous
        compilation.  At this time, the CLSI server returns an error 404 instead
        of a "compilation in progress" XML object, so this function hammers the
        server until a response is created by the server
        '''
        try:
            time.sleep(1)
            url = "http://"+self.host+"/output/"+id+"/response.xml"
            response = urllib2.urlopen(url).read()
        except urllib2.HTTPError, err:
            # Bug in the CLSI server, needs to continue to request the file
            if err.code == 404:
                self._debug("Error 404. Retrying")
                response = self.downloadID(id)
            else:
                sys.exit("Something happened! Error code "+err.code)
        except urllib2.URLError, err:
            sys.exit("Some other error happened: "+err.reason)
        return response

    def buildRequest(self, path, source):
        """
        Builds the XML request

        buildRequest() builds the XML request from the .tex source file.
        As of version 0.3, it searches for included file in the source
        file.  See findIncluded() documentation for more details.
        command
        As of verion 0.6, it uses either UTF-8 (whenever possible) or base 64 (as
        fallback encoding) for the input files
        """

        toCompile = [source+".tex"] + self.findIncluded(path+source+".tex")

        compile = Element("compile")

        token = SubElement(compile, "token")
        token.text = self.token

        options = SubElement(compile, "options")
        output = SubElement(options, "output-format")
        output.text = self.output
        compiler = SubElement(options, "compiler")
        compiler.text = self.compiler
        if not self.sync:
            async = SubElement(options, "asynchronous")
            async.text = 'true'
        resources = SubElement(compile, "resources")
        resources.set("root-resource-path", source+".tex")

        for file in toCompile:
            try:
                with open(path+file,"rb") as f:
                    cdata = f.read()
                    resource = SubElement(resources, "resource")
                    resource.set("path", file)
                    try:
                        content = cdata.decode('utf-8')
                        resource.set("encoding", 'utf-8')
                        resource.text = "<![CDATA["+content+"]]>"
                        self._debug(file+" encoded using UTF-8")
                    except ValueError:
                        content = base64.b64encode(cdata)
                        resource.set("encoding", 'base64')
                        resource.text = "<![CDATA["+content+"]]>"
                        self._debug(file+" encoded using base64")
                    finally:
                        resource.set("modified", time.strftime('%Y-%m-%d %H:%M:%S'))
            except IOError as e:
                self._debug("File included as "+file+" could not be found.")

        string = ElementTree.tostring(compile, encoding="utf-8", method="xml").replace('&gt;', '>').replace('&lt;', '<').replace('&amp;', '&')

        return string

    def fetchResult(self, response):
        """
        Parses the server response and downloads compiled files

        fetchResult() parses the CLSI server XML response and downloads the
        PDF file if the CLSI was able to compile the input file.  The log file
        is automatically deleted, unless the --log flag is passed to the script.
        If not, it downloads the log file and terminates the execution of the script.
        """

        filename = self.texsource

        tree = ElementTree.fromstring(response)
        for child in tree.getchildren():
            if child.tag == 'status':
                result = child.text
                # Compilation was successful
                if result == 'success':
                    for child in tree.getchildren():
                        if child.tag == 'output':
                            for child2 in child.getchildren():
                                self._debug("Saving output in :"+self.texpath+filename+"."+self.output)
                                output = child2.get('url')
                                urllib.urlretrieve(output, self.texpath+filename+"."+self.output)
                # Compilation not successful
                else:
                    for child in tree.getchildren():
                        if child.tag == 'error':
                            for child2 in child.getchildren():
                                if child2.tag == 'message':
                                    print('ERROR :\n\n')
                                    print(child2.text)
                        elif child.tag == 'logs':
                            for child2 in child.getchildren():
                                logs = child2.get('url')
                                log = urllib.urlopen(logs).read()
                                print(log)
                                if self.log:
                                    logFile = open(self.texpath+filename+".log", 'w')
                                    logFile.write(log)
                                    logFile.close()
                    sys.exit(1)
            if child.tag == 'logs':
                for child2 in child.getchildren():
                    logs = child2.get('url')
                    log = urllib.urlopen(logs).read()
                    print(log)
                    if self.log:
                        logFile = open(self.texpath+filename+".log", 'w')
                        logFile.write(log)
                        logFile.close()

    def findIncluded(self, file):
        """
        Finds the included files and compiler options

        findIncluded() scans the source file for included files.
        At this time (v0.3), it supports \input, \include, \includeonly, \thebibliography
        commands.
        If the included file is required by the LaTeX compiler but does not need to be
        included in the .tex file (e.g., a .sty file) use the command %\include{my.sty}
        to pass the my.sty file to the CLSI compiler.
        If no file extension is passes, this function will append the file extension
        .tex to files included with the commands \input, \include, and \includeonly
        and the file extension .bib for the files included with \thebibliography.
        Verson 0.8.1 adds support for embedded compiler options in the latex
        sorce code. To specify an option, use the command
        %rlatex: cmd options
        """
        try:
            load_profile = open(file, "r")
        except IOError:
            sys.exit("File "+ file  +" is not readable. Does it exist?")
        read_it = load_profile.read()
        myFiles = set() 
        for line in read_it.splitlines():
            if "\\graphicspath" in line:
                self._debug("Graphics path found at "+line)
                self.graphicspath += self._parse(line)
            if "\\DeclareGraphicsExtensions" in line:
                # This will overwrite default values
                self.graphicextensions = self._parse(line)
                self._debug("Graphic extensions now "+ ', '.join(self.graphicextensions))
            if "\\includegraphics" in line:
                self._debug("Include graphics found at "+line)
                file = self._parse(line)[0]
                for p in self.graphicspath:
                    self._debug("Searching for file "+p+file)
                    if "." in file:  # If file has an extension, keep it
                        if os.path.exists(p+file):
                            self._debug("File "+p+file+" exists")
                            myFiles.add(p+file)
                    else:
                        for ext in self.graphicextensions:
                            if os.path.exists(p+file+ext):
                                self._debug("File "+p+file+ext+" exists")
                                myFiles.add(p+file+ext)
            elif "\\include" in line or "\\input" in line:
                self._debug("Include found at "+line)
                try:
                    file = self._parse(line)[0]
                    if "." in file:  # If file has an extension, keep it
                        myFiles.add(file)
                    else:
                        myFiles.add(file+".tex")
                except AttributeError:
                    self._debug("Include found at "+line+" does not specify a file")
            elif "\\bibliography" in line:
                if not "\\bibliographystyle" in line:
                    self._debug("Include found at "+line)
                    try:
                        file = self._parse(line)[0]
                        if file.endswith(('.bib')):  # If file has an extension, keep it
                            myFiles.add(file)
                        else:
                            myFiles.add(file+".bib")
                    except AttributeError:
                        self._debug("Skipping "+line+". It does not specify a file")
            elif "%rlatex" in line:
                self._debug("RLatex command found at "+line)
                cmd = shlex.split(line)
                if cmd[1] == 'compiler':
                    self.compiler = cmd[2]
                    self._debug("Compiler set to "+self.compiler)
                elif cmd[1] == 'output':
                    self.output = cmd[2]
                    if self.output != "pdf":
                        self.graphicextensions = ['.eps']
                        print(self.graphicextensions)
                        sys.exit()
                    self._debug("output set to "+self.output)
                elif cmd[1] == 'include':
                    self._debug("including file "+cmd[2])
                    if "." in cmd[2]:  # If file has an extension, keep it
                        myFiles.add(cmd[2])
                    else:
                        myFiles.add(cmd[2]+".tex")   # Fallback extension is .tex
        myFiles= list(myFiles)
        self._debug("Included files :"+', '.join(myFiles))
        return myFiles

def main():
    """
    Main function
    """

    fsm = rlatex()
    fsm.compile(sys.argv)

if __name__ == "__main__":
    main()
