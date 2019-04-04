# narrativeReaper
Scan and delete narrative sessions which have not been active for a period of time.  Use -h for usage.

To use the Docker image, run a command like below.  The Docker socket is required to exec into the nginx container.  Use a path in /kb/module/work for --pickleFilePath to keep the file persistent on the host.

    docker run --rm -v /var/run/docker.sock:/var/run/docker.sock -v $HOME/tmp:/kb/module/work  kbase/narrativereaper [reapNarratives.py args]

To do:

* use a lock to prevent two processes clobbering the pickle file
* use the docker Python library instead of subprocess to talk to the nginx container (or maybe use the Rancher API?)
* have an option to run in an infinite loop, sleeping N minutes then running reapNarratives.py ?
