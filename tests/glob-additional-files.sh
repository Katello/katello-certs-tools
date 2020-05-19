#!/bin/bash

# Reproducer for https://projects.theforeman.org/issues/15932

DIRECTORY=$(mktemp -d)
trap "rm -rf $DIRECTORY" EXIT
cd $DIRECTORY

set -xe

INSTALL_RPMS=$([ -f /etc/redhat-release ] && [ -x /usr/bin/yum ] && [[ $(id -u) == 0 ]] && echo "true" || echo "false")

assert_file() {
  local filename="$1"
  if [[ ! -e "$filename" ]] ; then
    echo "File $filename not found"

    if [[ -x /usr/bin/tree ]] ; then
      tree
    fi

    exit 1
  fi

  if [[ "${INSTALL_RPMS}" == "true" ]]; then
    yum install -y "$filename"
  fi
}

# clean up any potential conflicts
if [[ "${INSTALL_RPMS}" == "true" ]]; then
  yum remove -y katello-default-ca katello-httpd-ssl-key-pair-$HOSTNAME
fi

katello-ssl-tool --gen-ca -p file:/etc/pki/katello/private/katello-default-ca.pwd --force --ca-cert-dir /etc/pki/katello-certs-tools/certs --set-common-name example.com --ca-cert katello-default-ca.crt --ca-key katello-default-ca.key --ca-cert-rpm katello-default-ca --set-country US --set-state "North Carolina" --set-city Raleigh --set-org Katello --set-org-unit SomeOrgUnit

assert_file ssl-build/katello-default-ca-1.0-1.noarch.rpm

# Foreman Proxy client cert

katello-ssl-tool --gen-client -p file:/etc/pki/katello/private/katello-default-ca.pwd --ca-cert-dir /etc/pki/katello-certs-tools/certs --set-common-name foo.example.com --ca-cert katello-default-ca.crt --ca-key katello-default-ca.key --set-country US --set-state "North Carolina" --set-city Raleigh --set-org FOREMAN --set-org-unit FOREMAN_PROXY --cert-expiration 36500 --server-rpm $HOSTNAME-foreman-proxy-client

assert_file ssl-build/$HOSTNAME/$HOSTNAME-foreman-proxy-client-1.0-1.noarch.rpm

# Foreman Proxy server cert

katello-ssl-tool --gen-server -p file:/etc/pki/katello/private/katello-default-ca.pwd --ca-cert-dir /etc/pki/katello-certs-tools/certs --set-common-name foo.example.com --ca-cert katello-default-ca.crt --ca-key katello-default-ca.key --set-country US --set-state "North Carolina" --set-city Raleigh --set-org FOREMAN --set-org-unit SMART_PROXY --cert-expiration 36500 --server-rpm $HOSTNAME-foreman-proxy

# Client certs and server certs conflict
if [[ "${INSTALL_RPMS}" == "true" ]]; then
  yum -y remove $HOSTNAME-foreman-proxy-client
fi

assert_file ssl-build/$HOSTNAME/$HOSTNAME-foreman-proxy-1.0-1.noarch.rpm
