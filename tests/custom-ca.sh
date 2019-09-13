#!/bin/bash

DIRECTORY=$(mktemp -d)
trap "rm -rf $DIRECTORY" EXIT
cd $DIRECTORY

set -xe

INSTALL_RPMS=$([ -f /etc/redhat-release ] && [ -x /usr/bin/yum ] && [[ $(id -u) == 0 ]] && echo "true" || echo "false")

for i in `seq 1 4`; do
  katello-ssl-tool --gen-ca -p file:/etc/pki/katello/private/katello-default-ca.pwd --force --ca-cert-dir /etc/pki/katello-certs-tools/certs --set-common-name example.com --ca-cert katello-default-ca.crt --ca-key katello-default-ca.key --ca-cert-rpm katello-default-ca --set-country US --set-state "North Carolina" --set-city Raleigh --set-org Katello --set-org-unit SomeOrgUnit

  if [[ "${INSTALL_RPMS}" == "true" ]]; then
    yum install -y $(ls -1t ./ssl-build/katello-default-ca-*.noarch.rpm|head -n1)
  fi

done

test -e ssl-build/katello-default-ca-1.0-4.noarch.rpm

for i in `seq 1 4`; do
  katello-ssl-tool --gen-server -p file:/etc/pki/katello/private/katello-default-ca.pwd --ca-cert-dir /etc/pki/katello-certs-tools/certs --set-common-name foo.example.com --ca-cert katello-default-ca.crt --ca-key katello-default-ca.key --set-country US --set-state "North Carolina" --set-city Raleigh --set-org Katello --set-org-unit SomeOrgUnit --cert-expiration 36500

  if [[ "${INSTALL_RPMS}" == "true" ]]; then
    yum install -y $(ls -1t ./ssl-build/$HOSTNAME/katello-httpd-ssl-key-pair-$HOSTNAME-*.noarch.rpm|head -n1)
  fi
done

test -e ssl-build/$HOSTNAME/katello-httpd-ssl-key-pair-$HOSTNAME-1.0-4.noarch.rpm

for i in `seq 1 4`; do
  katello-ssl-tool --gen-client -p file:/etc/pki/katello/private/katello-default-ca.pwd --ca-cert-dir /etc/pki/katello-certs-tools/certs --set-common-name foo.example.com --ca-cert katello-default-ca.crt --ca-key katello-default-ca.key --set-country US --set-state "North Carolina" --set-city Raleigh --set-org Katello --set-org-unit SomeOrgUnit --cert-expiration 36500
done

test -e ssl-build/$HOSTNAME/katello-httpd-ssl-key-pair-$HOSTNAME-1.0-8.noarch.rpm

if [[ -x /usr/bin/tree ]] ; then
	tree
fi
