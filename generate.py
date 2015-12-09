#!/usr/bin/env python

# example command
# ./generate.py -i redirects_export.csv -o migration_source_url -n url -r 302 -s nginx

# TODO: support "gone" and "seeother" statuses
# TODO: handle multiple domains?

from urlparse import urlparse
import sys
import csv
import argparse

redirects = [ "301", "permanent", "302", "temporary", "temp", "redirect" ]
servers   = [ "apache", "nginx" ]

parser = argparse.ArgumentParser(description='Generate web server redirects from a CSV of old and new URLs')
parser.add_argument( '-i', '--input',      required=True,  help='Input file name' )
parser.add_argument( '-o', '--old',        required=True,  help='Old URL column. If integer given, assumed to be column number starting at 1, otherwise assumed to be column label.' )
parser.add_argument( '-n', '--new',        required=True,  help='New URL column. If integer given, assumed to be column number starting at 1, otherwise assumed to be column label.' )
parser.add_argument( '-d', '--delimiter',  required=False, help='Delimiter' )
parser.add_argument( '-p', '--depth',      required=False, help='Depth' )
parser.add_argument( '-q', '--quote-char', required=False, help='Quote character' )
parser.add_argument( '-s', '--server',     required=False, help='Server type: ' + ", ".join(servers) )
parser.add_argument( '-r', '--redirect',   required=False, help='Return code or status: ' + ", ".join(redirects) )
args = parser.parse_args()

# set default parameters
if args.delimiter is None:
  args.delimiter = ','
if args.quote_char is None:
  args.quote_char = '"'
if args.server is None:
  args.server = 'nginx'
if args.depth is None:
  args.depth = "3"
if args.redirect is None:
  args.redirect = "302"

# validate server and redirect type
if args.server not in servers:
  sys.exit( "Server must be one of: " + ", ".join(servers) )
if args.redirect in redirects:
  if args.server == "apache":
    if args.redirect in [ "temporary", "redirect" ]:
      args.redirect = "temp"
  if args.server == "nginx":
    if args.redirect == "301":
      args.redirect = "permanent"
    if args.redirect in [ "302", "temporary", "temp" ]:
      args.redirect = "redirect"
else:
  sys.exit( "Return must be one of: " + ", ".join(redirects) )

with open(args.input, 'rb') as f:
  # detect presence of header row and rewind
  has_header = csv.Sniffer().has_header( f.read(1024) )
  f.seek(0)
  lines = csv.reader(f, delimiter=',', quotechar='"')
  # convert given column labels to column numbers
  if has_header:
    headers = lines.next()
  try:
    args.old = int( args.old ) - 1
  except ValueError:
    try: # nonint implies header row
      args.old = headers.index(args.old)
    except ValueError:
      print "No column header '%s'" % args.old
      sys.exit(0)
  # check if integer or try to convert label to integer
  try:
    args.new = int( args.new ) - 1
  except ValueError:
    try: # nonint implies header row
      args.new = headers.index(args.new)
    except ValueError:
      print "No column header '%s'" % args.new
      sys.exit(0)
  # parse data
  try:

    # Here through deleter() mostly from http://stackoverflow.com/a/7794859/172602

    # First build a list of all url segments: final item is the title/url dict
    paths = []
    for line in lines:
      # extract URLs
      ( old, new ) = ( line[args.old], line[args.new] )
      # remove scheme, domain and parameters
      old = urlparse(old).path
      new = urlparse(new).path

      split = old.split('/', int(args.depth) + 1 )
      paths.append(split[1:-1]) # ignore first since data starts with /
      #paths.append(split)
      paths[-1].append( (split[-1], new) )

    # Loop over these paths, building the format as we go along
    root = {}
    for path in paths:
      branch = root.setdefault(path[0], [{}, []])
      for step in path[1:-1]:
        branch = branch[0].setdefault(step, [{}, []])
      branch[1].append(path[-1])

    # As for the cleanup: because of the alternating lists and
    # dicts it is a bit more complex, but the following works:
    def walker(coll):
      if isinstance(coll, list):
        for item in coll:
          yield item
      if isinstance(coll, dict):
        for item in coll.itervalues():
          yield item

    def deleter(coll):
      for data in walker(coll):
        if data == [] or data == {}:
          coll.remove(data)
        deleter(data)

    deleter(root)

  except csv.Error as e:
    sys.exit( "file %s, line %d: %s" % ( args.input, lines.line_num, e ) )


  # Output redirects, really confusingly
  def printLocation(data, depth=0, prefix=None):

    if isinstance(data, tuple):
      ( old, new ) = data
      if prefix is None:
        old = "/%s" % ( old )
      else:
        old = "/%s/%s" % ( prefix, old )
      if args.server == "apache":
        print "%sRedirect %s %s %s" % ( ' ' * depth, args.redirect, old, new )
      if args.server == "nginx":
        print "%srewrite ^%s$ %s %s;" % ( ' ' * depth, old, new, args.redirect )

    if isinstance(data, dict):
      for key in data:

        if isinstance(key, tuple):
          path = None
          # remove indentation when not splitting into location blocks
          depth = -3 
        else:
          if prefix is None:
            path = key
          else:
            path = prefix + '/' + key
          if args.server == "apache":
            print "%s<Location /%s>" % ( ' ' * depth, path )
          if args.server == "nginx":
            print "%slocation ^~ /%s {" % ( ' ' * depth, path )

        printLocation(data[key], depth+1, path)

        if not isinstance(key, tuple):
          if args.server == "apache":
            print "%s</Location>" % ( ' ' * depth )
          if args.server == "nginx":
            print "%s}" % ( ' ' * depth )

    if isinstance(data, list):
      for item in data:
        printLocation(item, depth+1, prefix)

  printLocation(root)


