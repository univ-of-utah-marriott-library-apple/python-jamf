# Python-jamf Docker Container

These files are for testing only. The keyring inside of the docker image depends on keyrings.alt, and I'm not sure if that is securely encrypted.

## Starting the container

Start a container

	cd python-jamf
	docker-compose run --rm python-jamf

You will have an interactive shell. The cwd is /python-jamf.

## Setting it up

Run these commands inside of the container.

If you downloaded and installed python-jamf using git, you wont have jamf/VERSION. You need to create that first.

	git describe --tags > jamf/VERSION

We need to fix this in the future. To setup the config, do this.

	cp jamf/setconfig.py .

Then you can run it.

	./setconfig.py

If you get an error regarding check_version() then you need to create jamf/VERSION (see above).

You can connect to your jamf server like normal. Or you can connect to a Jamf Pro server that's running in a different container (see https://github.com/magnusviri/dockerfiles/tree/main/jamfpro).

Enter your Jamf Pro hostname and credentials. If you run Jamf Pro in a container, you can get it's IP with this command (run on the host).

	docker inspect jamfpro_jamfpro_1 | grep IPA

## Testing that it works

To test the connection, use this.

	./setconfig.py -t

If you see something like this then you are good to go.

	{'accounts': {'groups': None, 'users': {'user': {'id': '1', 'name': 'james'}}}}

If you see the following you need to fix your settings.

	HTTPSConnectionPool(host='172.18.0.2', port=8080): Max retries exceeded with url: /JSSResource/accounts (Caused by SSLError(SSLError(1, '[SSL: WRONG_VERSION_NUMBER] wrong version number (_ssl.c:1129)')))

Be sure that your hostname has the correct settings for http/https and port. If you're using a container it's probably http://example.com:8080. If it's a productions server it's probably https://example.com:8443.

## Doing stuff.

If you copy jctl to the host python-jamf folder you will be able to run it inside the container.

Run unit tests.

	python -m unittest discover -s tests -p '*_test.py'