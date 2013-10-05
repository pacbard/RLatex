# RLatex

A python interface to a LaTeX CLSI server

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

If any of the server, api_url, and token are omitted, you will be
asked to provide them.

RLatex supports multiple compilers and output formats:
```
    pdflatex    pdf
    latex       dvi, pdf, ps
    xelatex     pdf
    standalone  png, jpg, tiff, bmp
```
If the compiler and/or the output format are not specified as arguments,
RLatex will use ```pdflatex``` as compiler and ```pdf``` as output format. For this
reason, most user will not need to specify a compiler or output formats.

If the ```standalone``` compiler option is selected, please refer to the ```standalone``` 
package documentation for more information.

### Asynchronous Compilation
Asynchronous compilation is supported using the parameter ```--async```.  In this 
case, the connection to the server will be closed once the files are uploaded and
the script will check at given time intervals if the compilation was completed.

Please, note that at this time there is a bug in the CLSI server.  Asynchronous
compilation returns a **404 error** if the compilation is in progress instead of the
expected "**compilation in progress**" message.

### Compile to Windows Executible
It is possible to compile this script to a one Windows executible using ```pyinstaller```.


***

See the RLaTeX documentation for more details on usage and limitations
of rlatex.

## License

MIT: http://pacbard.mit-license.org/
