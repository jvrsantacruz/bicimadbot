NAME := $(shell python setup.py --name)
VERSION := $(shell python setup.py --version)
DISTNAME := $(NAME)-$(VERSION)-full
DIST := $(DISTNAME).tar.gz
DISTFILE := dist/$(DIST)
WHEELHOUSE := wheelhouse
DEPLOYER := arl
SERVER := $(DEPLOYER)@$(HOST)
INSTALLDIR := /home/$(DEPLOYER)/$(NAME)
VENV := $(INSTALLDIR)/$(VERSION)
CURR_VENV := $(INSTALLDIR)/current
RUNAPP := $(INSTALLDIR)
CURR_BIN := $(CURR_VENV)/bin/bmad


build:
	mkdir -p dist/$(DISTNAME)
	pip wheel . --wheel-dir dist/$(DISTNAME) --find-links $(WHEELHOUSE)
	tar cvzf dist/$(DIST) -C dist $(DISTNAME)
	rm -fr dist/$(DISTNAME)


deploy:
	# Check version wasn't already deployed
	ssh $(SERVER) test ! -d $(VENV)

	# Upload bundle
	scp $(DISTFILE) $(SERVER):/tmp/$(DIST)

	# Uncompress bundle
	ssh $(SERVER) "rm -rf $(DISTNAME) \
	               && mkdir -p $(DISTNAME) \
	               && tar --strip-components=1 -xzf /tmp/$(DIST) -C $(DISTNAME)"
	ssh $(SERVER) rm -f /tmp/$(DIST)
	ssh $(SERVER) mkdir -p $(INSTALLDIR)

	# Install app into a virtualenv
	ssh $(SERVER) virtualenv --python python3 $(VENV)
	ssh $(SERVER) $(VENV)/bin/pip install wheel
	ssh $(SERVER) $(VENV)/bin/pip install $(DISTNAME)/$(NAME)-*.whl --find-links $(DISTNAME)

	# Set new version as current version
	ssh $(SERVER) ln -sfn $(VENV) $(CURR_VENV)


clean:
	rm -fr dist
	find -name *.pyc -delete


start:
	@echo "starting bmad"
	ssh $(SERVER) sudo supervisorctl start $(NAME)

stop:
	@echo "stopping bmad"
	ssh $(SERVER) sudo supervisorctl stop $(NAME)

restart:
	@echo "restarting bmad"
	ssh $(SERVER) sudo supervisorctl restart $(NAME)

status:
	@echo "status bmad"
	ssh $(SERVER) sudo supervisorctl status $(NAME)


version:
	ssh $(SERVER) $(CURR_BIN) --version


allup: build deploy restart status


help:
	@echo "build   - builds app distributable"
	@echo "deploy  - puts last distributable to production"
	@echo "clean   - cleans all object files"
	@echo "start   - starts service"
	@echo "stop    - stops all service processes"
	@echo "restart - stops all processes and starts a new one"
	@echo "allup   - build deploy restart status"
