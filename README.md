# Redirects generator

A Python command line utility to generate from a CSV file a list of web server redirects optionally grouped into location blocks of arbitrary depth. It also served as my introduction to Python; apologies for clunky code.

## Use

Despite best efforts, content URLs often change after migrating between content management systems such as Movable Type, Drupal and WordPress. In such cases of impermanent permalinks, it is best to ensure attempts to visit the old web addresses are redirected correctly. 

As part of the migration, the old URL can be added into a new custom field such that the new system can generate a CSV file of old and new URLs. This utility might be especially useful for large numbers of redirects, which can be automatically grouped into location blocks based on the directory structure.

The output can be placed directly in a web server configuration file or included via a directive such as this Nginx one: `include /etc/nginx/conf.d/redirects.subconf;`

## Arguments

The options can be placed in any order on the command line.

### Required

* `-i`, `--input`  
  Input file name
* `-o`, `--old`  
  Old URL column. If an integer given, it is assumed to be the column number (starting with 1), otherwise it is assumed to be the column label.
* `-n`, `--new`  
  New URL column. If an integer given, it is assumed to be the column number (starting with 1), otherwise it is assumed to be the column label.

### Optional

* `-d`, `--delimiter`  
  Delimiter
* `-p`, `--depth`  
  Depth of nested location blocks. `0` puts all redirects at the root, with no nesting.
* `-q`, `--quote-char`  
  Quote character
* `-s`, `--server`  
  Server type: `apache` or `nginx`
* `-r`, `--redirect`  
  Return code or status: `301`, `permanent`, `302`, `temporary`, `temp` or `redirect`

### Nesting

I haven't done performance testing to see if grouping redirects into location blocks makes a difference, but it seemed reasonable and at least helps with organization! If anyone has occassion to test server response time while tens of thousands of redirects are in effect, please let me know. Thanks!

## Example

    python generate.py
      -i example/redirects_export.csv
      -o migration_source_url
      -n url
      -r permanent
      -s nginx
      -p 1
      > example/redirects.subconf

See [redirects.subconf](example/redirects.subconf) for an example of what the above command produces from the source [redirects_export.csv](example/redirects_export.csv).