#!/bin/bash

set -e

export LC_ALL=en_US.UTF-8

TEST_ON_EL=$([ -f /etc/redhat-release ] && [ -x /usr/bin/yum ] && echo "true" || echo "false")
PYTHON=python

if [[ "${TEST_ON_EL}" == "true" ]]; then
  . /etc/os-release
  if [[ $VERSION_ID == 8 ]] ; then
    # TODO: where's docbook-utils on EL8?
    PACKAGES="python3 python3-setuptools"
    PYTHON="python3"
    # This is where Python 3 on EL8 installs packages to
    mkdir -p /usr/local/lib/python3.6/site-packages
  elif [[ $VERSION_ID == 7 ]] ; then
    PACKAGES="docbook-utils python-setuptools"
  fi

  yum install -y openssl rpm-build tree $PACKAGES
fi

if [[ -x /usr/bin/docbook2man ]] ; then
  docbook2man katello-ssl-tool.sgml
else
  touch katello-ssl-tool.1
fi

$PYTHON setup.py install

for filename in tests/* ; do
	if [[ -x $filename ]] ; then
		echo "=== TEST: $filename ==="
		$filename
	else
		echo "File $filename is not executable"
		exit 1
	fi
done
