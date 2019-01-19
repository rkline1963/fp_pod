#!/usr/bin/python

import feedparser
import time
from subprocess import check_output
import subprocess as sp
import sys
import pathlib

flist = []
try:
    f = open("fp.conf", "r")
except:
    print "No fp.conf file"
    exit()
for line in f:
    if line[0] == "#": # Skip comment lines
        continue
    y=line.split()
    if len(y) > 2: # there should be 3 or 4 fields in the line
        flist.append(y)
        for i in y:
            print i
    
db_file = 'fp.db'

def slugify(value):
    """
    Normalizes string, converts to lowercase, removes non-alpha characters,
    and converts spaces to hyphens. First part of django's slugify function
    suggested on stack exchange
    """
    import unicodedata
    import re # needed for Python 2.7 not needed for Python 3
    value = unicodedata.normalize('NFKD', value).encode('ascii', 'ignore')
    value = unicode(re.sub('[^\w\s-]', '', value).strip().lower())
    value = unicode(re.sub('[-\s]+', '-', value))
    return(value)

def rtn_filename(title):
    # Content management systems put bad characters into titles that must be
    # removed using slugify from django framework stripping out the symhc-
    # from Stuff You Missed in History Class classics episodes
    fname = slugify(title).replace("symhc-", "")
    if len(fname)>58:
        fname = fname[:58]
    return fname

def rtn_numstr(num):
    if num < 10:
        dstr = "000"
    elif num < 100:
        dstr = "00"
    elif num < 1000:
        dstr = "0"
    else:
        dstr = ""
    return "%s%d" % (dstr, num)

def post_is_in_db(title, db):
    with open(db, 'r') as database:
        for line in database:
            if title in line:
                return True
    return False

def post_is_in_dir(title, cdir):
    for line in sp.check_output("ls %s" % cdir, shell=True).split("\n"):
        if title in line:
            return True
    return False

# return true if the title is in the database with a timestamp > limit
def post_is_in_db_with_old_timestamp(title, db):
    with open(db, 'r') as database:
        for line in database:
            if title in line:
                ts_as_string = line.split('|', 1)[1]
                ts = long(ts_as_string)
                if current_timestamp - ts > limit:
                    return True
    return False

ppath = pathlib.Path("./podcasts")
if not ppath.is_dir(): # is the ./podcasts directory there
    if ppath.exists(): # is there a non-directory named ./podcasts
        sp.call("rm ./podcasts", shell=True)
    sp.call("mkdir ./podcasts", shell=True)        

for i in flist:
    feed_url = i[0]
    castdir = "./podcasts/%s" % i[1] # assumes you are running in a directory
    # with a subdirectory named podcasts which has a directory for each podcast
    # like Chess Griffin's mashpodder does
    castpath = pathlib.Path(castdir)
    if not castpath.is_dir(): # if there is not a directory named castdir
        if castpath.exists(): # if there is a non-directory named castdir
            sp.call("rm %s" % castdir, shell=True) # delete the non-directory
        sp.call("mkdir %s" % castdir, shell=True) # create the directory
    db = "%s/%s" % (castdir, db_file)
    dbpath = pathlib.Path(db)
    if not dbpath.is_file(): # if there is no file for the db create one
        sp.call("touch %s" % db, shell=True)
    numstr = i[2]
    if numstr.split()[0] == "all":
        nflag = False
    else:
        nflag = True
        try:
            ncast = int(numstr)
        except:
            ncast = 10
            print "Bad number of casts field, using 10"
    if nflag:
        print "%d casts to get" % ncast
    else:
        print "get all casts"
    if len(i) > 3:
        if i[3].split()[0] == "rename":
            rflag = True
            print "Rename casts"
        else:
            rflag = False
            print "Don't rename"
    else: # this is for backward compatibility with mashpodder mp.conf files
        rflag = False
        print "No rename field, don't rename"
    print "url is %s" % feed_url
    feed = feedparser.parse(feed_url)
    print feed.feed['title']
    fnum = len(feed.entries)
    print "%d items in feed" % fnum
    count = 0
    add_to_db = []
    for j in feed.entries:
        count += 1
        if nflag and count > ncast:
            break
        x = j.links
        url = x[-1]['href']
        print "podcast %d url: %s" % (count, url)
        if rflag: # Rename files from feeds with random hash filenames
            # Assume these feeds have all episodes in the feed so we can get a
            # unique episode number from the position in the feed.
            ep_num = fnum - count + 1 
            ttl = rtn_filename(j.title)
            file_to_get = url.split("/")[-1]
            # How stuff works does updated episodes with "?updated..." appended
            # after the .mp3 so ditch what's after ?
            """if "?" in file_to_get:
                file_to_get = file_to_get.split("?")[0]"""
            extension = file_to_get.split(".")[-1]
            if "?" in extension:
                extension = extension.split("?")[0]
            new_name = "%s_%s.%s" % (rtn_numstr(ep_num), ttl, extension)
            print "new name = %s\n" % new_name
            if not post_is_in_db(new_name, db):
                if not post_is_in_dir(new_name, castdir):
                    # only get file if unrenamed file isn't there from another
                    # podcatcher
                    try:
                        output = sp.check_output("wget %s" % url, shell = True,
                                             cwd = castdir)
                        wsuccess = True
                    except:
                        print "Error with wget command for %s" % url
                        wsuccess = False
                print "\nRename %s ---> %s\n" % (file_to_get, new_name)
                try:
                    if pathlib.Path("%s/%s" % (castdir, new_name)).is_file():
                        sp.call("rm %s", shell = True, cwd = castdir)
                    output = sp.check_output("mv %s %s" % (file_to_get,
                                                           new_name), shell
                                             = True, cwd = castdir)
                except:
                    print "Error with delete or rename of file command!"
                    wsuccess = False
                if wsuccess:
                    add_to_db.append(new_name)
        else: # Leave file name as is for feeds with meaningful file names
            file_to_get = url.split("/")[-1]
            if len(file_to_get.split("?"))>1:
                sflag = True
                file_to_get=file_to_get.split("?")[0]
            else:
                sflag = False
            if not post_is_in_db(file_to_get, db):
                # check if file is there from another podcatcher included
                # to allow a transition to this script from mashpodder without
                # downloading all episodes again
                if not post_is_in_dir(file_to_get, castdir):
                    try:
                        output = sp.check_output("wget %s" % url, shell = True,
                                             cwd = castdir)
                        wsuccess=True
                        if sflag:
                            sp.call("mv %s %s" % (url.split("/")[-1],
                                                  file_to_get), shell = True,
                                    cwd = castdir)
                    except:
                        wsuccess=False
                    if wsuccess:
                        add_to_db.append(file_to_get)
    if len(add_to_db) > 0:
        f = open(db, 'a')
        for fname in add_to_db:
            f.write("%s\n" % fname)
        f.close
    
