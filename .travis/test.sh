#!/bin/bash

set -e

export LC_ALL=en_US.UTF-8

TEST_ON_EL=$([ -f /etc/redhat-release ] && [ -x /usr/bin/yum ] && echo "true" || echo "false")

if [[ "${TEST_ON_EL}" == "true" ]]; then
  yum install -y docbook-utils openssl rpm-build python-setuptools
fi

docbook2man katello-ssl-tool.sgml

python setup.py install

for filename in tests/* ; do
	if [[ -x $filename ]] ; then
		$filename
	else
		echo "File $filename is not executable"
		exit 1
	fi
done
