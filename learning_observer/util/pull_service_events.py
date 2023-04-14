#!/usr/bin/env python
# pull_service_events.py
# Collin F. Lynch
#
# The service log contains a complete dump of
# events including the authentication which is
# needed for the restream.  This will simply
# pull out the objects then restream to a file.


# imports
# -------------------------------------------
import re

AUTH_LINE_RE = re.compile("^Auth {")
EVENT_LINE_RE = re.compile("^event {")
JSON_CLEAN_RE = re.compile('(?<!\\\\)\'')
NONE_FIX_RE = re.compile(' None')
TRUE_FIX_RE = re.compile(' True')
FALSE_FIX_RE = re.compile(' False')


def pull_service_events(InputStream):
    """
    Pull events from the specified input stream 
    we extract all auth and event items.
    """
    for Line in InputStream:

        if (AUTH_LINE_RE.match(Line) != None):
            ResultLine = JSON_CLEAN_RE.sub('\"', Line[5:-1])
            ResultLine = NONE_FIX_RE.sub(" null", ResultLine)
            ResultLine = TRUE_FIX_RE.sub(" true", ResultLine)
            ResultLine = FALSE_FIX_RE.sub(" false", ResultLine)
            print(ResultLine)
        elif (EVENT_LINE_RE.match(Line) != None):
            ResultLine = JSON_CLEAN_RE.sub('\"', Line[6:-1])
            ResultLine = NONE_FIX_RE.sub(" null", ResultLine)
            ResultLine = TRUE_FIX_RE.sub(" true", ResultLine)
            ResultLine = FALSE_FIX_RE.sub(" false", ResultLine)
            print(ResultLine)


def pull_service_events_file(InputFile):
    """
    Pull events from the specified file.
    """
    with open(InputFile) as Infile:
        pull_service_events(Infile)


if __name__ == "__main__":
    import sys
    pull_service_events_file(sys.argv[1])
    
    
