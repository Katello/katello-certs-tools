#!/bin/bash

set -e

export LC_ALL=en_US.UTF-8

PYTHON=python3

if [[ -f /etc/redhat-release ]]; then
  . /etc/os-release
  if [[ $VERSION_ID == "8.10" ]] ; then
    REPOS="--enablerepo=powertools"
  else
    REPOS=""
  fi

  dnf install ${REPOS} -y openssl rpm-build tree python3 python3-setuptools docbook-utils glibc-langpack-en
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
