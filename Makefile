build:	#build for the current platform (on that platform)
	docker build -t jrcichra/smartcar_python_base containers/python_base
	docker-compose -f docker-compose-test.yml build
build-rpi:	# build for a pi (on a pi)
	docker build -t jrcichra/smartcar_python_base containers/python_base
	docker-compose -f docker-compose-rpi.yml build
build-all: # use docker buildx script (which removes docker-ce and installs the nightly) - only run from CI
	bash -x build.sh
build-all-rpi:	# use docker buildx script for the rpi (which removes docker-ce and installs the nightly) - only run from CI
	bash -x build.sh rpi

test:	#use docker-compose to start up all the containers and the test container
	docker-compose -f docker-compose-test.yml up --abort-on-container-exit --exit-code-from gpio

default: build
