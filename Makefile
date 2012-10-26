
#
# airScore Makefile 
#
# Author: Geoff Wong 2007/2008
# Copying: GPLv2, see the file Copying included
# with this software, or see www.gnu.org if it wasn't provided.
#

TARGET=airScore
DIR=airscore
VERSION=0.96

MYSQLPASSWORD=xxxxx
INSTALL=install
HTROOT=/var/www
CGIBIN=/usr/lib/cgi
TRACKDIR=/var/airscore/tracks/
MAKE=make

TARGET_OS=$(shell uname)
OBJPATH=obj/$(TARGET_OS)/
DEFS=-D_REENTRANT -D$(TARGET_OS)

HTML=$(shell echo *.html *.png *.css)
PHP_SRC=$(shell echo *.php *.js)
BIN=$(shell echo *.pl *.pm)
SQL=$(shell grep -l MYSQLPASSWORD *.php *.pl *.pm *.sql)

LIBS=

all: passwords install
	$echo Installing scripts in $(HTROOT) and $(CGIBIN)


database: passwords
	@echo Creating the database for the first time
	mysql -u root -p < foo.sql

install: 
	mkdir -p $(CGIBIN)
	mkdir -p $(TRACKDIR)
	$(INSTALL) -m 0755 $(BIN) $(CGIBIN)
	mkdir -p $(HTROOT)
	$(INSTALL) -m 0644 $(HTML) $(HTROOT)
	$(INSTALL) -m 0644 $(PHP_SRC) $(HTROOT)
	cp -r images $(HTROOT)

package:
	-rm ../$(DIR)-$(VERSION)
	cd ..; ln -s app $(DIR)-$(VERSION)
	cd ..; tar zcfh $(DIR)_$(VERSION).tar.gz $(DIR)-$(VERSION) --exclude debian --exclude .svn --exclude bin --exclude build
	cd ..; tar zcfh $(DIR)_$(VERSION).orig.tar.gz $(DIR)-$(VERSION) --exclude debian --exclude .svn --exclude bin --exclude build
	pwd; debuild -m$(MAINTAINER) -aarmel -i.svn -I.svn -us -uc
	-rm ../$(DIR)-$(VERSION)
	-cd ..; mv $(DEBS) package

release:
	$(shell cd ..; tar jcf $(TARGET)-$(VERSION).tar.bz2 airscore --exclude=.svn)

tags: $(SRC)
	ctags $^

clean:
	rm -f $(TARGET) $(OBJ)

.PHONY:

passwords:
	@./submacro.sh MYSQLPASSWORD $(MYSQLPASSWORD)
	@./submacro.sh CGIBIN $(CGIBIN)
	@./submacro.sh VERSION $(VERSION)

