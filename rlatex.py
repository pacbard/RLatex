#!/usr/bin/env python

from __future__ import print_function
import sys, httplib, getopt
from xml.etree.ElementTree import Element, SubElement, Comment
from xml.etree import ElementTree
from xml.dom import minidom
import urllib
import os.path
import re
import logging

__applicationName__ = "rlatex"

__doc__ = """
Process a LaTex file using a CLSI server.

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
    -d, --debug:      	debug version of the script

Exclude http:// from the server URL, since `http://' will be prepended to
by the script.
At this time, https:// are not supported by the CLSI server.

You can hard-code the filename from which to read login information into
the rlatex script. Command-line arguments take precedence over
the contents of that file. See the RLaTeX documentation for formatting
details.

If any of the server, username, and password are omitted, you will be
asked to provide them.

The CLSI interface supports the following compilers and outputs:
    pdflatex    pdf
    latex       dvi, pdf, ps
    xelatex     pdf

See the RLaTeX documentation for more details on usage and limitations
of rlatex."""

__version__ = "0.4"
__date__ = "October 7th, 2012"
__website__ = "http://pacbard.github.com/RLatex"

__author__ = "Emanuele 'pacbard' Bardelli (bardellie at gmail dot com)"

__licenseName__ = "GPL v2"
__license__ = """
This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 2 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""

class FSM(object):
	"""	Implements a finite state machine.
		
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
	"""	Makes a transition based on the given input.
		
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
	"""	Init function
		
		__init__() initializes the class variables to None or False
		"""
		self.host, self.api_url, self.token, self.texsource, self.texpath = (None,) * 5
		self.log, self.debug = (False,) *2
		self.login = self.scriptPath()+'/login.txt'
		self.compiler = 'pdflatex'
		self.output = 'pdf'

	def compile(self, argv):
	"""	Compile function
		
		Compile function.  This wraps the compile task
		@param argv The command line arguments passed by the user
		"""
		self.manageArgv(argv)
		
		self.loadLogin()
		
		XMLrequest = self.buildRequest(self.texpath, self.texsource)
		toDownload = self.do_request(XMLrequest)
		self.fetchResult(toDownload)
	
	def loadLogin(self):
	"""	Loads login information or asks them through command line
			
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
				print('Login information found in file {0}.'.format(self.login))
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
			print (login, " not found")
		if not self.host:
			self.host = raw_input('Enter server: ')
		if not self.api_url:
			self.api_url = raw_input('Enter API URL: ')
		if not self.token:
			self.token = raw_input('Enter token:  ')

		## Screen confirmation of the settings
		print("Server: ", self.host)
		print("API URL: ", self.api_url)
		print("Token: ", self.token)
	
	def manageArgv(self, argv):
	"""	Argument management
		"""
		# Checks if all the flags are correct
		try:
			opts, file = getopt.getopt(argv[1:], 'hlds:a:t:f:l:c:o:',
								['help', 'log', 'debug', 'server=', 'api_url=', 'token=', 'file=', 'compiler=', 'output='])
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
				sys.exit()
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
				logging.basicConfig(filename='debug.log',level=logging.DEBUG, format='%(asctime)s\n%(message)s\n', datefmt='%m/%d/%Y %I:%M:%S %p')
						
		# Splits the argument in the path and the source
		self.texpath, self.texsource = os.path.split(file[0])
		
		if self.texpath != "":
			self.texpath += "/"
		
		# Gets the file name without the extension
		self.texsource = os.path.splitext(self.texsource)[0]
		
	def scriptPath(self):
	"""	Returns the script installation path
		
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
	"""	Posts the XML request
		
		do_request posts the XML request to the CLSI server.
		This is based on HTTP XML Post request, by www.forceflow.be
		It returns the server response to the request.
		If the --debug flag is set, it will dump the XML request and the 
		server response in the debug file.
		"""

		webservice = httplib.HTTP(self.host)
		webservice.putrequest("POST", self.api_url)
		webservice.putheader("Host", self.host)
		webservice.putheader("User-Agent","Remote Laxet 0.1a")
		webservice.putheader("Content-type", "text/xml; charset=\"UTF-8\"")
		webservice.putheader("Content-length", "%d" % len(xml_request))
		webservice.endheaders()
		webservice.send(xml_request)
		statuscode, statusmessage, header = webservice.getreply()
		result = webservice.getfile().read()
		if self.debug:
			logging.info("XML request")
			logging.info(xml_request)
			logging.info("XML request result")
			logging.info(result)
		return result

	def buildRequest(self, path, source):
	"""	Builds the XML request
		
		buildRequest() builds the XML request from the .tex source file.
		As of version 0.3, it searches for included file in the source
		file.  See findIncluded() documentation for more details.
		command
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
		
		resources = SubElement(compile, "resources")
		resources.set("root-resource-path", source+".tex")
		
		for file in toCompile:
			resource = SubElement(resources, "resource")
			resource.set("path", file)
			
			cdata = open(path+file,"r").read()
				
			resource.text = "\n<![CDATA[\n"+cdata.decode('utf-8','ignore')+"\n]]>\n"
		
		string = ElementTree.tostring(compile, encoding='utf-8', method="xml").replace('&gt;', '>').replace('&lt;', '<').replace('&amp;', '&')

		return string

	def fetchResult(self, response):
	"""	Parses the server response and downloads compiled files
		
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
				if result == 'success':
					for child in tree.getchildren():
						if child.tag == 'output':
							for child2 in child.getchildren():
								output = child2.get('url')
								urllib.urlretrieve (output, filename+"."+self.output)
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
								log = urllib.urlopen(logs)
								print(log.read())
								if self.log:
									localFile = open(filename+".log", 'w')
									localFile.write(log.read())
									localFile.close()
					sys.exit()
			if child.tag == 'logs':
				for child2 in child.getchildren():
					logs = child2.get('url')
					urllib.urlretrieve (logs, filename+".log")
					log = open(filename+".log","r").read()
					if not self.log:
						os.remove(filename+".log")
					print(log)

	def findIncluded(self, file):
	"""	Finds the included files
		
		findIncluded() scans the source file for included files.
		At this time (v0.3), it supports \input, \include, \includeonly, 
		\thebibliography commands.
		If the included file is required by the LaTeX compiler but does not need to be
		included in the .tex file (e.g., a .sty file) use the command %\include{my.sty}
		to pass the my.sty file to the CLSI compiler.
		If no file extension is passes, this function will append the file extension
		.tex to files included with the commands \input, \include, and \includeonly
		and the file extension .bib for the files included with \thebibliography.
		"""
		load_profile = open(file, "r")
		read_it = load_profile.read()
		myFiles = []
		for line in read_it.splitlines():
			if "\\include" in line:
				if self.debug:
					logging.info("Include found at "+line+"\n")
				value = re.search(r'\{(.+)\}', line)
				if ".tex" in value.group(1):
					myFiles.append(value.group(1))
				else:
					myFiles.append(value.group(1)+".tex")
				continue
			elif "\\includeonly" in line:
				if self.debug:
					logging.info("Include found at "+line+"\n")
				value = re.search(r'\{(.+)\}', line)
				if ".tex" in value.group(1):
					myFiles.append(value.group(1))
				else:
					myFiles.append(value.group(1)+".tex")
				continue
			elif "\\input" in line:
				if self.debug:
					logging.info("Include found at "+line)
				value = re.search(r'\{(.+)\}', line)
				if ".tex" in value.group(1):
					myFiles.append(value.group(1))
				else:
					myFiles.append(value.group(1)+".tex")
				continue
			elif "\\bibliography" in line:
				if not "\\bibliographystyle" in line:
					if self.debug:
						logging.info("Bibliography fount at "+line+"\n")
					value = re.search(r'\{(.+)\}', line)
					if ".bib" in value.group(1):
						myFiles.append(value.group(1))
					else:
						myFiles.append(value.group(1)+".bib")
				continue
		return myFiles
	
def main():
"""	Main function """

	fsm = rlatex()
	fsm.compile(sys.argv)

if __name__ == "__main__":
    main()