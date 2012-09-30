Python interface to a LaTeX CLSI server

Usage: python rlatex.py [options] inputfile.tex

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

Exclude http:// from the server URL, since the script will prepend 
`http://' . At this time, https:// are not supported by the CLSI server.

You can hard-code the filename from which to read login information into
the rlatex script. Command-line arguments take precedence over
the contents of that file. See the RLaTeX documentation for formatting
details.

If any of the server, api_url, and token are omitted, you will be
asked to provide them.

RLatex supports multiple compilers and output formats:
    pdflatex    pdf
    latex       dvi, pdf, ps
    xelatex     pdf
If the compiler and/or the output format are not specified as arguments,
RLatex will use pdflatex as compiler and pdf as output format. For this
reason, most user will not need to specify a compiler or output formats.

See the RLaTeX documentation for more details on usage and limitations
of rlatex.