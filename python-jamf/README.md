# Python-jamf Docker Container

These files are for testing only. The keyring inside of the docker image depends on keyrings.alt, and I'm not sure if that is securely encrypted.

## Usage

Start a container

	cd python-jamf
	docker-compose run --rm python-jamf

You will have an interactive shell. The cwd is /python-jamf. If you copy jctl to the host python-jamf folder you will be able to run it inside the container.

You can connect to your jamf server like normal. Or you can connect to a Jamf Pro server that's running in a different container (see https://github.com/magnusviri/dockerfiles/tree/main/jamfpro).

If you run Jamf Pro in a container, you can get it's IP with this command (run on the host).

	docker inspect jamfpro_jamfpro_1 | grep IPA
