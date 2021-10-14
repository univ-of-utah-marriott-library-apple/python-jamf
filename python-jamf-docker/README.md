# Python-jamf Docker Container

These images are for development and testing. The keyring inside of the docker image depends on keyrings.alt, and I'm not sure if that is securely encrypted. So don't use this for production.

There are 3 containers in this project.

## python-jamf-dev

Will bind mount ../ to python-jamf. I use this for most of the crazy development because the files can be edited and I know that it wont load any other python-jamf.

	cd docker
	docker-compose run --rm python-jamf-dev

You will have an interactive shell. The cwd is /python-jamf.

If you downloaded and installed python-jamf using git, you wont have jamf/VERSION. You need to create that first (the github image below does this automatically).

	git describe --tags > jamf/VERSION

This will rebuild the image.

	docker-compose build python-jamf-dev

You can move on to the setup.py section.
	
## python-jamf-github

Downloads the files from github into the container. I use this if I want to do tests on a clean version.

	cd docker
	docker-compose run --rm python-jamf-github

You will have an interactive shell. The cwd is /python-jamf.

This will rebuild the image.

	docker-compose build python-jamf-github

You can move on to the setup.py section.

## python3

A blank python3 container with keyrings.alt installed. I use this to test `pip install python-jamf`.

	cd docker
	docker-compose run --rm python3

You will have an interactive shell. The cwd is /.

	pip install python-jamf

This will rebuild the image.

	docker-compose build python3

You can move on to the conf-python-jamf section.

## setup.py

To install python-jamf (which really means conf-python-jamf), run this command.

	python setup.py install

## conf-python-jamf

Then you can configure python-jamf.

	conf-python-jamf

Enter the url of your jamf server, your username, and your password.

## Jamf Pro in a container.

You can connect to your normal jamf server. Or you can connect to a Jamf Pro server that's running in a different container.  Read about [Jamf Pro in a container](https://github.com/magnusviri/dockerfiles/tree/main/jamfpro).

You can get the IP of the containerized server with this command (run on the host).

	docker inspect jamfpro_jamfpro_1 | grep IPA

## Testing that it works

To test the connection, use this.

	conf-python-jamf -t

If you see something like this then you are good to go.

	{'accounts': {'groups': None, 'users': {'user': {'id': '1', 'name': 'james'}}}}

If you see the following you need to fix your settings.

	HTTPSConnectionPool(host='172.18.0.2', port=8080): Max retries exceeded with url: /JSSResource/accounts (Caused by SSLError(SSLError(1, '[SSL: WRONG_VERSION_NUMBER] wrong version number (_ssl.c:1129)')))

Be sure that your hostname has the correct settings for http/https and port. If you're using a container it's probably http://example.com:8080. If it's a productions server it's probably https://example.com:8443.

## Doing stuff

Run unit tests.

	python -m unittest discover -s tests -p '*_test.py'