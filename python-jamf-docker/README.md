# python-jamf Docker Containers

These images are for development and testing. The keyring inside of the docker image depends on keyrings.alt, and I'm not sure if that is securely encrypted. So don't use this for production.

## The 3 Containers

### python-jamf-dev

Will bind mount ../ to python-jamf. I use this for most of the active development because the files can be edited on the host. I also use it for testing before I commit/push to github.

	cd docker
	docker-compose run --rm python-jamf-dev

You will have an interactive shell. The cwd is /python-jamf.

If you downloaded and installed python-jamf using git, you probably wont have jamf/VERSION. You need to create that first.

	git describe --tags > jamf/VERSION

This will rebuild the image.

	docker-compose build python-jamf-dev

To install python-jamf (which really means put conf-python-jamf in /usr/local/bin), run this command.

	python setup.py install

### python-jamf-github

Downloads the files from github into the container. By editing the Dockerfile for this container, you can change the version you want to test by altering the "git checkout main" line (and then rebuild the image). Because there is no volume mounted on the host you can't edit these files from the host. So I mostly use this container to test the github repo is working correctly.

	cd docker
	docker-compose run --rm python-jamf-github

You will have an interactive shell. The cwd is /python-jamf.

This will rebuild the image.

	docker-compose build python-jamf-github

### python3

A blank python3 container with keyrings.alt installed. I use this to test `pip install python-jamf`.

	cd docker
	docker-compose run --rm python3

You will have an interactive shell. The cwd is /.

This will install the [pypi python-jamf package](https://pypi.org/project/python-jamf/).

	pip install python-jamf

This will rebuild the image.

	docker-compose build python3

## Configuring your host

Run this command to configure python-jamf.

	conf-python-jamf

Enter the url of your jamf server, your username, and your password.

To test the connection, use this.

	conf-python-jamf -t

If you see something like this then you are good to go.

	{'accounts': {'groups': None, 'users': {'user': {'id': '1', 'name': 'james'}}}}

If you see the following you need to fix your settings.

	HTTPSConnectionPool(host='172.18.0.2', port=8080): Max retries exceeded with url: /JSSResource/accounts (Caused by SSLError(SSLError(1, '[SSL: WRONG_VERSION_NUMBER] wrong version number (_ssl.c:1129)')))

Be sure that your hostname has the correct settings for http/https and port. If you're using a certificates (like a production server should) it's probably https://example.com:8443. If you're not using certificates, like on a containerized server, it's probably http://example.com:8080 or http://example.com:80.

### Containerized Jamf Pro

These containers were tested with on-prem, jamfcloud, and [containerized Jamf Pro](https://github.com/magnusviri/dockerfiles/tree/main/jamfpro) servers. To use these containers with the containerized Jamf Pro server, use the following setting.

__http://jamfpro:8080__

Because these containers are connecting to the jamfpro_jamfnet network, the same network used by the Jamf Pro container, you need to connect to the port within the container, not the port exposed on the host. So, for example, this is part of my jamfpro definition.

	jamfpro:
	  networks:
		- jamfnet
	  ports:
		- "80:8080"

The python-jamf containers connect to "http://jamfpro:8080" to talk to the jamfpro container. Outside of the container (on the host), you'd connect to "http://localhost:80".

Also, you can get the IP of the jamfpro container with this command (run on the host).

	docker inspect jamfpro_jamfpro_1 | grep IPA

## Doing stuff

Run unit tests.

	python -m unittest discover -s tests -p '*_test.py'