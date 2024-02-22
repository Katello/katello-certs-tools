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
#
# katello-ssl-tool general library
#
# $Id$

from __future__ import print_function
import contextlib
import os
import sys
import tempfile

from katello_certs_tools.timeLib import DAY, now, secs2days, secs2years


class KatelloSslToolException(Exception):
    """ general exception class for the tool """
    code = 100


errnoGeneralError = 1
errnoSuccess = 0


def fixSerial(serial):
    """ fixes a serial number this may be wrongly formatted """

    if not serial:
        serial = '00'

    if serial.find('0x') == -1:
        serial = '0x'+serial

    # strip the '0x' if present
    serial = serial.split('x')[-1]

    # the string might have a trailing L
    serial = serial.replace('L', '')

    # make sure the padding is correct
    # if odd number of digits, pad with a 0
    # e.g., '100' --> '0100'
    if len(serial) % 2 != 0:
        serial = '0'+serial

    return serial


#
# NOTE: the Unix epoch overflows at: 2038-01-19 03:14:07 (2^31 seconds)
#

def secsTil18Jan2038():
    """ (int) secs til 1 day before the great 32-bit overflow
        We are making it 1 day just to be safe.
    """
    return int(2**31 - 1) - now() - DAY


def daysTil18Jan2038():
    "(float) days til 1 day before the great 32-bit overflow"
    return secs2days(secsTil18Jan2038())


def yearsTil18Jan2038():
    "(float) approximate years til 1 day before the great 32-bit overflow"
    return secs2years(secsTil18Jan2038())


def gendir(directory):
    "makedirs, but only if it doesn't exist first"
    if not os.path.exists(directory):
        try:
            os.makedirs(directory, 0o700)
        except OSError as e:
            print("Error: %s" % (e, ))
            sys.exit(1)


@contextlib.contextmanager
def disabled_rpm_macros():
    directory = os.path.expanduser('~')
    macros = os.path.join(directory, '.rpmmacros')
    if os.path.exists(macros):
        yield
    else:
        fd, temporary_file = tempfile.mkstemp(prefix='RENAME_ME_BACK_PLEASE',
                                              suffix='.rpmmacros', dir=directory)
        fd.close()
        os.rename(macros, temporary_file)
        try:
            yield
        finally:
            os.rename(temporary_file, macros)


@contextlib.contextmanager
def chdir(newdir):
    "A context manager to temporarily work in another directory"
    cwd = os.getcwd()
    try:
        os.chdir(newdir)
    finally:
        os.chdir(cwd)


try:
    TemporaryDirectory = tempfile.TemporaryDirectory
except AttributeError:
    # Python 3.2 introduced TemporaryDirectory but copied here for Python 2.7
    import shutil as _shutil
    import warnings as _warnings
    import weakref as _weakref

    class TemporaryDirectory(object):
        """Create and return a temporary directory.  This has the same
        behavior as mkdtemp but can be used as a context manager.  For
        example:

            with TemporaryDirectory() as tmpdir:
                ...

        Upon exiting the context, the directory and everything contained
        in it are removed.
        """

        def __init__(self, suffix=None, prefix=None, dir=None):
            self.name = tempfile.mkdtemp(suffix, prefix, dir)
            self._finalizer = _weakref.finalize(
                self, self._cleanup, self.name,
                warn_message="Implicitly cleaning up {!r}".format(self))

        @classmethod
        def _cleanup(cls, name, warn_message):
            _shutil.rmtree(name)
            _warnings.warn(warn_message, ResourceWarning)

        def __repr__(self):
            return "<{} {!r}>".format(self.__class__.__name__, self.name)

        def __enter__(self):
            return self.name

        def __exit__(self, exc, value, tb):
            self.cleanup()

        def cleanup(self):
            if self._finalizer.detach():
                _shutil.rmtree(self.name)
