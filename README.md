A single-file, simple python script for counting lines of code.

# Installation
1. Open `loc.py` and verify that it's not doing anything
   malicious -- search for imports, make sure it's not
   doing any network stuff, etc.
2. Download `loc.py`, make sure it's executable and (optionally)
   put it somewhere on your `$PATH`; e.g. `.loca/bin/loc.py`,
   `/usr/bin/loc.py`, etc.

# Usage
```
./loc.py [OPTIONS] PATH...

Count the lines of code in files and directories.

The targeted files and directories are specified by passing
one or more PATH arguments.

OPTIONS:
-x/--exclude PATH .... Exclude PATH from being counted.
                       Multiple PATHs can be excluded by passing
                       this option multiple times.
-b/--count-blank ..... Count blank lines.
                       Blank lines are NOT counted by default!
-e/--by-ext .......... Display number of lines for each separate
                       file extension.
-h/--help ............ Display this usage message.
--debug .............. Display debug log messages.
--license ............ Display this software's license.
```
(as displayed by calling `loc.py -h`.)

