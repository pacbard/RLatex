Python interface to a LaTeX CLSI server

Usage: rlatex.py [options] inputfile.tex

Options:

    -h, --help:         print this message
    -s, --server:       the CLSI server to contact
    -a, --api_url:      API URl on the server
    -t, --token:     	your token
    -f, --file:         get login information from a file
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

See the RLaTeX documentation for more details on usage and limitations
of rlatex.