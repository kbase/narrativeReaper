# narrativeReaper
Scan and delete narrative sessions which have not been active for a period of time.  Use -h for usage.

To use the Docker image, run a command like below.  The Docker socket is required to exec into the nginx container.  Use a path in /kb/module/work for --pickleFilePath to keep the file persistent on the host.

    docker run --rm -v /var/run/docker.sock:/var/run/docker.sock -v $HOME/tmp:/kb/module/work  kbase/narrativereaper [reapNarratives.py args]

To do:

* use a lock to prevent two processes clobbering the pickle file
