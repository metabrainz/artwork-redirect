Cover Art Archive URL redirect service
======================================

This service will redirect from coverartarchive.org URLs to
archive.org URLs, taking into account MBID redirects caused by
releases merges.

This URL:

   http://coverartarchive.org/release/5b07fe49-39a9-47a6-97b3-e5005992fb2a/front.jpg

should redirect to:

   http://archive.org/download/mbid-5b07fe49-39a9-47a6-97b3-e5005992fb2a/mbid-5b07fe49-39a9-47a6-97b3-e5005992fb2a-2270157148.jpg


## Install

To install this service, you will need to have the following python
packages installed:

    cherrypy  psycopg2  sqlalchemy  werkzeug

Depending on your os version you can install them with the system
package manager, or you may have to install them manually.


### Ubuntu 10.04 LTS or later

On Ubuntu you can install these with the following command:

    sudo apt-get install python-cherrypy3 python-psycopg2 python-sqlalchemy python-werkzeug

As we are currently running this service on Ubuntu 10.04 LTS,
requirements.txt has been pinned at the versions shipped with that
version of Ubuntu.  If you want to run/develop/test against those
exact versions on a more recent Ubuntu or on a different GNU/Linux
distribution or a different operating system, use virtualenv:

    virtualenv ~/path/to/virtualenv
    ~/path/to/virtualenv/bin/pip install -r requirements.txt


## Running the server

CherryPy is used as the WSGI server. To deploy, simply copy
coverart_redirect.conf.dist to coverart_redirect.conf, edit the
settings to point to a MusicBrainz postgres install and where to
listen for connections.

Then run coverart_redirect_server.py to run the service. All logging
goes to stdout, including stacktraces, so its suitable for running
inside of daemontools.

If you've installed some of the required packages with virtualenv, run
the server using python from the virtualenv directory:

    ~/path/to/virtualenv/bin/python coverart_redirect_server.py


## Running the tests

I use nose as a test runner, though other test runners may work.

To install nose on Ubuntu:

    sudo apt-get install python-nose

I prefer to run it like this:

    nosetests --nologcapture --nocapture

You should get output like this:

    .....
    ----------------------------------------------------------------------
    Ran 5 tests in 12.221s
    
    OK

If you're using a virtualenv you probably have to install nose in
there as well:

    ~/path/to/virtualenv/bin/pip install nose
    ~/path/to/virtualenv/bin/nosetests --nologcapture --nocapture
