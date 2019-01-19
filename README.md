# fp_pod
Python podcast client using the feedparser module
fp_pod.py looks for a config file fp.conf in the current directory and based on its contents downloads files from each
feed in the fp.conf file to a different directory for each feed under the podcasts subdirectory of the current directory
if the directory for the feed doesn't exist, it will be created. There is some trapping of errors and it prints diagnostic
messages to standard output as it runs.
