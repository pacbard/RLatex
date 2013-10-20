# RLatex

A CLSI command line client

Usage: `python rlatex.py [options] inputfile.tex`

Options:
```
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
```
You can hard-code the filename from which to read login information into
the rlatex script. Command-line arguments take precedence over
the contents of that file. See the RLaTeX documentation for formatting
details.

### Configuration

A ```login.txt``` configuration file can be included in the root directory
of this script. Three options need to be included in this file:
```
server = 'clsi.example.com'
api_url = '/clsi/compile'
token = 'your_token'
```

If any required configuration option are missing or no login file is provided, 
you will be asked to input them interactively.

### Compiler Options

RLatex supports multiple compilers and output formats. Please contact the
CLSI maintainer for more information regarding supported compilers and output
formats.

If the compiler and/or the output format are not specified as arguments,
RLatex will use ```pdflatex``` as compiler and ```pdf``` as output format. For this
reason, most user will not need to specify a compiler or output formats.

It is also possible to specify the compiler and output format within the LaTeX
file. To do so, include the following code in any LaTeX file
```
    %rlatex: compiler cmd
    %rlatex: output ext
```

### Asynchronous Compilation
Asynchronous compilation is supported using the parameter ```--async```.  In this 
case, the connection to the server will be closed once the files are uploaded and
the script will check at given time intervals if the compilation was completed.

Please, note that at this time there is a bug in the CLSI server.  Asynchronous
compilation returns a **404 error** if the compilation is in progress instead of the
expected "**compilation in progress**" message.

### Compile to Executible
It is possible to compile this script using ```pyinstaller --onefile rlatex.py```.


***

See the RLaTeX documentation for more details on usage and limitations
of rlatex.

## License

RLatex - A CLSI command line client.

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
