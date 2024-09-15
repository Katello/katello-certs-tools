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

import os
import shutil
import sys


def _file_contents_match(first, second):
    if os.path.getsize(first) != os.path.getsize(second):
        return False

    with open(first) as first_fp, open(second) as second_fp:
        return first_fp.read() == second_fp.read()


def cleanupAbsPath(path):
    """ take ~taw/../some/path/$MOUNT_POINT/blah and make it sensible.

        Path returned is absolute.
        NOTE: python 2.2 fixes a number of bugs with this and eliminates
              the need for os.path.expanduser
    """

    if path is None:
        return None
    return os.path.abspath(
             os.path.expanduser(
               os.path.expandvars(path)))


def cleanupNormPath(path, dotYN=0):
    """ take ~taw/../some/path/$MOUNT_POINT/blah and make it sensible.

        Returned path may be relative.
        NOTE: python 2.2 fixes a number of bugs with this and eliminates
              the need for os.path.expanduser
    """
    if path is None:
        return None
    path = os.path.normpath(
             os.path.expanduser(
               os.path.expandvars(path)))
    if dotYN and not (path and path[0] == '/'):
        dirs = path.split('/')
        if dirs[:1] not in (['.'], ['..']):
            dirs = ['.'] + dirs
        path = '/'.join(dirs)
    return path


def rotateFile(filepath, depth=5, suffix='.', verbosity=0):
    """ backup/rotate a file
        depth (-1==no limit) refers to num. of backups (rotations) to keep.

        Behavior:
          (1)
            x.txt (current)
            x.txt.1 (old)
            x.txt.2 (older)
            x.txt.3 (oldest)
          (2)
            all file stats preserved. Doesn't blow away original file.
          (3)
            if x.txt and x.txt.1 are identical (size or checksum), None is
            returned
    """

    # check argument sanity (should really be down outside of this function)
    if not filepath or not isinstance(filepath, str):
        raise ValueError("filepath '%s' is not a valid arguement" % filepath)
    if not isinstance(depth, int) or depth < -1 or depth > sys.maxsize-1 or depth == 0:
        raise ValueError("depth must fall within range "
                         "[-1, 1...%s]" % (sys.maxsize-1))

    # force verbosity to be a numeric value
    verbosity = verbosity or 0
    if not isinstance(verbosity, int) or verbosity < -1 or verbosity > sys.maxsize-1:
        raise ValueError('invalid verbosity value: %s' % (verbosity))

    filepath = cleanupAbsPath(filepath)
    if not os.path.isfile(filepath):
        raise ValueError("filepath '%s' does not lead to a file" % filepath)

    pathNSuffix = filepath + suffix
    pathNSuffix1 = pathNSuffix + '1'

    if verbosity > 1:
        sys.stderr.write("Working dir: %s\n"
                         % os.path.dirname(pathNSuffix))

    # is there anything to do? (existence, then size, then checksum)
    if os.path.exists(pathNSuffix1) and os.path.isfile(pathNSuffix1) \
            and _file_contents_match(filepath, pathNSuffix1):
        # nothing to do
        if verbosity:
            sys.stderr.write("File '%s' is identical to its rotation. "
                             "Nothing to do.\n" % os.path.basename(filepath))
        return None

    # find last in series (of rotations):
    last = 0
    while os.path.exists('%s%d' % (pathNSuffix, last+1)):
        last = last+1

    # percolate renames:
    for i in range(last, 0, -1):
        os.rename('%s%d' % (pathNSuffix, i), '%s%d' % (pathNSuffix, i+1))
        if verbosity > 1:
            filename = os.path.basename(pathNSuffix)
            sys.stderr.write("Moving file: %s%d --> %s%d\n" % (filename, i,
                                                               filename, i+1))

    # blow away excess rotations:
    if depth != -1:
        last = last+1
        for i in range(depth+1, last+1):
            path = '%s%d' % (pathNSuffix, i)
            os.unlink(path)
            if verbosity:
                sys.stderr.write("Rotated out: '%s'\n" % (
                    os.path.basename(path)))

    # do the actual rotation
    shutil.copy2(filepath, pathNSuffix1)
    if os.path.exists(pathNSuffix1) and verbosity:
        sys.stderr.write("Backup made: '%s' --> '%s'\n"
                         % (os.path.basename(filepath),
                            os.path.basename(pathNSuffix1)))

    # return the full filepath of the backed up file
    return pathNSuffix1
