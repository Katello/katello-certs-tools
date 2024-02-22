#!/bin/bash

set -e

export LC_ALL=en_US.UTF-8

TEST_ON_EL=$([ -f /etc/redhat-release ] && [ -x /usr/bin/yum ] && echo "true" || echo "false")
PYTHON=python3

if [[ "${TEST_ON_EL}" == "true" ]]; then
  . /etc/os-release
  if [[ $VERSION_ID == 8 ]] ; then
    # TODO: where's docbook-utils on EL8?
    PACKAGES=""
    # This is where Python 3 on EL8 installs packages to
    mkdir -p /usr/local/lib/python3.6/site-packages
  elif [[ $VERSION_ID == 9 ]] ; then
    PACKAGES="docbook-utils"
  fi

  dnf install -y openssl rpm-build tree python3 python3-setuptools $PACKAGES
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
