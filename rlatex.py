#!/usr/bin/env python
##
## Copyright (C) 2012 by Emanuele Bardelli <bardellie@gmail.com>
## 
## This program is free software: you can redistribute it and/or modify it
## under the terms of the GNU General Public License as published by the
## Free Software Foundation, either version 2 of the License, or (at your
## option) any later version.
## 
## This program is distributed in the hope that it will be useful, but
## WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General
## Public License for more details.
## 
## You should have received a copy of the GNU General Public License along
## with this program.  If not, see <http://www.gnu.org/licenses/>.
## 

from __future__ import print_function
import sys, httplib, getopt
from xml.etree.ElementTree import Element, SubElement, Comment
from xml.etree import ElementTree
from xml.dom import minidom
import urllib
import os.path

#########################################################################
# You can provide a filename here and the script will read your login   #
# information from that file. The format must be:                       #
#                                                                       #
# server = 'foo.com'                                                    #
# api_url = 'api_url/loc'                                               #
# token = 'token'                                                       #
#                                                                       #
# You can omit one or more of those lines, use " quotes, and put hash   #
# marks at the beginning of a line for comments. Command-line args      #
# take precedence over information from the file.                       #
#########################################################################
def filePath():
	if hasattr(sys, 'frozen'):
		basis = sys.executable
	else:
		basis = os.path.realpath(__file__)
	return(os.path.split(basis)[0])
login_info_file = filePath()+'/login.txt'

usage = """Process a LaTex file using a CLSI server.

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
    -v, --verbose:      verbose version of the script

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

def do_request(xml_request):
	"""HTTP XML Post request, by www.forceflow.be"""
	webservice = httplib.HTTP(HOST)
	webservice.putrequest("POST", API_URL)
	webservice.putheader("Host", HOST)
	webservice.putheader("User-Agent","Remote Laxet 0.1a")
	webservice.putheader("Content-type", "text/xml; charset=\"UTF-8\"")
	webservice.putheader("Content-length", "%d" % len(xml_request))
	webservice.endheaders()
	webservice.send(xml_request)
	statuscode, statusmessage, header = webservice.getreply()
	result = webservice.getfile().read()
	if VERBOSE:
		LOGFILE.write("XML request\n")
		LOGFILE.write(xml_request)
		LOGFILE.write("\nXML request result\n")
		LOGFILE.write(result)
	return result

def do_xml(source):
	compile = Element("compile")
	
	token = SubElement(compile, "token")
	token.text = TOKEN
	
	options = SubElement(compile, "options")
	output = SubElement(options, "output-format")
	output.text = OUTPUT
	compiler = SubElement(options, "compiler")
	compiler.text = COMPILER
	
	resources = SubElement(compile, "resources")
	resources.set("root-resource-path", os.path.basename(source)+".tex")
	
	resource = SubElement(resources, "resource")
	resource.set("path", os.path.basename(source)+".tex")
	
	cdata = open(source+".tex","r").read()
		
	resource.text = "<![CDATA[\n"+cdata.decode('utf-8','ignore')+"\n]]>"
	
	string = ElementTree.tostring(compile, encoding='utf-8', method="xml").replace('&gt;', '>').replace('&lt;', '<').replace('&amp;', '&')
	return string

def do_parse(xmltext, filename):
	tree = ElementTree.fromstring(xmltext)
	for child in tree.getchildren():
		if child.tag == 'status':
			result = child.text
			if result == 'success':
				for child in tree.getchildren():
					if child.tag == 'output':
						for child2 in child.getchildren():
							output = child2.get('url')
							urllib.urlretrieve (output, filename+"."+OUTPUT)
			else:
				for child in tree.getchildren():
					if child.tag == 'error':
						for child2 in child.getchildren():
							if child2.tag == 'message':
								print('ERROR :\n\n')
								print(child2.text)	
								sys.exit(3)
		if child.tag == 'logs':
			for child2 in child.getchildren():
				logs = child2.get('url')
				urllib.urlretrieve (logs, filename+".log")
				log = open(filename+".log","r").read()
				if not LOG:
					os.remove(filename+".log")
				print(log)

try:
	opts, args = getopt.getopt(sys.argv[1:], 'hlvs:a:t:f:l:c:o:',
					['help', 'log', 'verbose', 'server=', 'api_url=', 'token=', 'file=', 'compiler=', 'output='])
except getopt.GetoptError as err:
	print(str(err), usage, sep='\n\n')
	sys.exit(2)
	
HOST, API_URL, TOKEN, COMPILER, OUTPUT = (None,) * 5
LOG = False
VERBOSE = False

for o, a in opts:
	if o in ('-h', '--help'):
		print(usage)
		sys.exit()
	elif o in ('-s', '--server'):
		HOST = a
	elif o in ('-a', '--api_url'):
		API_URL = a
	elif o in ('-t', '--token'):
		TOKEN = a
	elif o in ('-f', '--file'):
		login_info_file = a
	elif o in ('-l', '--log'):
		LOG = True
	elif o in ('-c', '--compiler'):
		COMPILER = a
	elif o in ('-o', '--output'):
		OUTPUT = a
	elif o in ('-v', '--verbose'):
		VERBOSE = True
		LOGFILE = open("rlatex.log","w+")

if len(args) != 1:
	print('Error: must specify exactly one file. Please specify options first.',usage, sep='\n\n')
	sys.exit(2)

if login_info_file:
	try:
		with open(login_info_file, 'r') as f:
			print('Login information found in file {0}.'.format(login_info_file))
			get_val = lambda x: x.split('=')[1].strip().strip('\'"')
			for line in f:
				if not line.startswith('#'):
					if line.startswith('server') and not HOST:
						HOST = get_val(line)
					if line.startswith('api_url') and not API_URL:
						API_URL = get_val(line)
					if line.startswith('token') and not TOKEN:
						TOKEN = get_val(line)
	except IOError as e:
		print (login_info_file, " not found")
if not HOST:
	HOST = raw_input('Enter server: ')
if not API_URL:
	API_URL = raw_input('Enter API URL: ')
if not TOKEN:
	TOKEN = raw_input('Enter token:  ')

# Default values if not passed through argument
if not COMPILER:
	COMPILER = 'pdflatex'
if not OUTPUT:
	OUTPUT = 'pdf'

print("Server: ", HOST)
print("API URL: ", API_URL)
print("Token: ", TOKEN)

if len(args) != 1:
	print('Error: must specify exactly one file. Please specify options first.',usage, sep='\n\n')
	sys.exit(2)

jobname = os.path.splitext(args[0])[0]
xml_request = do_xml(jobname)
result = do_request(xml_request)
do_parse(result, jobname)
if VERBOSE:
	LOGFILE.close()
