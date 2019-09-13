#!/bin/bash

HOSTNAME=host.example.com
RPM=$HOSTNAME-apache
CERT=cert.pem
REQ=cert.req
KEY=key.pem

DIRECTORY=$(mktemp -d)
trap "rm -rf $DIRECTORY" EXIT
cd $DIRECTORY

set -ex

mkdir -p ssl-build/$HOSTNAME
touch ssl-build/$HOSTNAME/$CERT ssl-build/$HOSTNAME/$REQ ssl-build/$HOSTNAME/$KEY

katello-ssl-tool --gen-server --set-hostname $HOSTNAME --server-cert $CERT --server-cert-req $REQ --server-key $KEY --server-rpm $RPM --rpm-only

if [[ -x /usr/bin/tree ]] ; then
	tree
fi

test -e ssl-build/$HOSTNAME/$RPM-1.0-1.src.rpm
test -e ssl-build/$HOSTNAME/$RPM-1.0-1.noarch.rpm
test ! -e ssl-build/$HOSTNAME/katello-httpd-ssl-archive-$HOSTNAME-1.0-1.tar
