#
# Copyright 2013 Red Hat, Inc.
#
# This software is licensed to you under the GNU General Public License,
# version 2 (GPLv2). There is NO WARRANTY for this software, express or
# implied, including the implied warranties of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. You should have received a copy of GPLv2
# along with this software; if not, see
# http://www.gnu.org/licenses/old-licenses/gpl-2.0.txt.
#
# Red Hat trademarks are not licensed under GPLv2. No permission is
# granted to use or replicate Red Hat trademarks that are incorporated
# in this software or its documentation.
#

from __future__ import print_function
import os
import rpm
import struct
import functools

# Expose a bunch of useful constants from rpm
error = rpm.error

# need this for rpm-pyhon < 4.6 (e.g. on RHEL5)
rpm.RPMTAG_FILEDIGESTALGO = 5011

# these values are taken from /usr/include/rpm/rpmpgp.h
# PGPHASHALGO_MD5             =  1,   /*!< MD5 */
# PGPHASHALGO_SHA1            =  2,   /*!< SHA1 */
# PGPHASHALGO_RIPEMD160       =  3,   /*!< RIPEMD160 */
# PGPHASHALGO_MD2             =  5,   /*!< MD2 */
# PGPHASHALGO_TIGER192        =  6,   /*!< TIGER192 */
# PGPHASHALGO_HAVAL_5_160     =  7,   /*!< HAVAL-5-160 */
# PGPHASHALGO_SHA256          =  8,   /*!< SHA256 */
# PGPHASHALGO_SHA384          =  9,   /*!< SHA384 */
# PGPHASHALGO_SHA512          = 10,   /*!< SHA512 */
PGPHASHALGO = {
  1: 'md5',
  2: 'sha1',
  3: 'ripemd160',
  5: 'md2',
  6: 'tiger192',
  7: 'haval-5-160',
  8: 'sha256',
  9: 'sha384',
  10: 'sha512'
}


class InvalidPackageError(Exception):
    pass


class RPM_Header:
    "Wrapper class for an rpm header - we need to store a flag is_source"
    def __init__(self, hdr, is_source=None):
        self.hdr = hdr
        self.is_source = is_source
        self.packaging = 'rpm'
        self.signatures = []
        self._extract_signatures()

    def __getitem__(self, name):
        return self.hdr[name]

    def __getattr__(self, name):
        return getattr(self.hdr, name)

    def __nonzero__(self):
        if self.hdr:
            return True
        else:
            return False

    def is_signed(self):
        if hasattr(rpm, "RPMTAG_DSAHEADER"):
            dsaheader = self.hdr["dsaheader"]
        else:
            dsaheader = 0
        if self.hdr["siggpg"] or self.hdr["sigpgp"] or dsaheader:
            return 1
        return 0

    def _extract_signatures(self):
        header_tags = [
            [rpm.RPMTAG_DSAHEADER, "dsa"],
            [rpm.RPMTAG_RSAHEADER, "rsa"],
            [rpm.RPMTAG_SIGGPG, "gpg"],
            [rpm.RPMTAG_SIGPGP, 'pgp'],
        ]
        for ht, sig_type in header_tags:
            ret = self.hdr[ht]
            if not ret:
                continue
            ret_len = len(ret)
            if ret_len < 17:
                continue
            # Get the key id - hopefully we get it right
            elif ret_len <= 65:  # V3 DSA signature
                key_id = ret[9:17]
            elif ret_len <= 72:  # V4 DSA signature
                key_id = ret[18:26]
            elif ret_len <= 536:  # V3 RSA/SHA256 signature
                key_id = ret[10:18]
            else:  # V4 RSA/SHA signature
                key_id = ret[19:27]

            key_id_len = len(key_id)
            key_format = "%dB" % key_id_len
            t = struct.unpack(key_format, key_id)
            key_format = "%02x" * key_id_len
            key_id = key_format % t
            self.signatures.append({
                'signature_type': sig_type,
                'key_id': key_id,
                'signature': ret
            })


SHARED_TS = None


def get_package_header(filename=None, file_stream=None, fd=None):
    """ Loads the package header from a file / stream / file descriptor
        Raises rpm.error if an error is found, or InvalidPacageError if package is
        busted
    """
    global SHARED_TS
    # XXX Deal with exceptions better
    if (filename is None and file_stream is None and fd is None):
        raise ValueError("No parameters passed")

    if filename is not None:
        f = open(filename)
    elif file_stream is not None:
        f = file_stream
        f.seek(0, 0)
    else:  # fd is not None
        f = None

    if f is None:
        os.lseek(fd, 0, 0)
        file_desc = fd
    else:
        file_desc = f.fileno()

    # don't try to use rpm.readHeaderFromFD() here, it brokes signatures
    # see commit message
    if not SHARED_TS:
        SHARED_TS = rpm.ts()
    SHARED_TS.setVSFlags(-1)

    rpm.addMacro('_dbpath', '/var/cache/rhn/rhnpush-rpmdb')
    try:
        hdr = SHARED_TS.hdrFromFdno(file_desc)
        rpm.delMacro('_dbpath')
    except RuntimeError:
        rpm.delMacro('_dbpath')
        raise

    if hdr is None:
        raise InvalidPackageError
    is_source = hdr[rpm.RPMTAG_SOURCEPACKAGE]

    return RPM_Header(hdr, is_source)


def hdrLabelCompare(hdr1, hdr2):
    """ take two RPMs or headers and compare them for order """

    if hdr1['name'] == hdr2['name']:
        try:
            hdr1 = [hdr1['epoch'], hdr1['version'].decode('utf-8'), hdr1['release'].decode('utf-8')]
            hdr2 = [hdr2['epoch'], hdr2['version'].decode('utf-8'), hdr2['release'].decode('utf-8')]
        except AttributeError:
            hdr1 = [hdr1['epoch'], hdr1['version'], hdr1['release']]
            hdr2 = [hdr2['epoch'], hdr2['version'], hdr2['release']]
        if hdr1[0]:
            hdr1[0] = str(hdr1[0])
        if hdr2[0]:
            hdr2[0] = str(hdr2[0])
        return rpm.labelCompare(hdr1, hdr2)
    elif hdr1['name'] < hdr2['name']:
        return -1
    return 1


hdrLabelCompareKey = functools.cmp_to_key(hdrLabelCompare)


def sortRPMs(rpms):
    """ Sorts a list of RPM files. They *must* exist.  """

    assert isinstance(rpms, type([]))
    return sorted(rpms, key=lambda rpm: hdrLabelCompareKey(get_package_header(rpm)))


def getInstalledHeader(rpmName):
    """ quieries the RPM DB for a header matching rpmName. """

    hdr = None
    ts = rpm.TransactionSet()
    mi = ts.dbMatch()
    mi.pattern("name", rpm.RPMMIRE_STRCMP, rpmName)
    for h in mi:
        hdr = h
    return hdr
