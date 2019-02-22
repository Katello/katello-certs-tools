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
import sys
import types
import shutil
import subprocess
import select
import tempfile
from checksum import getFileChecksum


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
    if not filepath or type(filepath) != type(''):
        raise ValueError("filepath '%s' is not a valid arguement" % filepath)
    if type(depth) != type(0) or depth < -1 \
      or depth > sys.maxint-1 or depth == 0:
        raise ValueError("depth must fall within range "
                         "[-1, 1...%s]" % (sys.maxint-1))

    # force verbosity to be a numeric value
    verbosity = verbosity or 0
    if type(verbosity) != type(0) or verbosity < -1 \
      or verbosity > sys.maxint-1:
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
    checksum_type = 'md5'       # FIXME: this should be configuation option
    if os.path.exists(pathNSuffix1) and os.path.isfile(pathNSuffix1) \
      and os.stat(filepath)[6] == os.stat(pathNSuffix1)[6] \
      and getFileChecksum(checksum_type, filepath) == \
          getFileChecksum(checksum_type, pathNSuffix1):
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


def rhn_popen(cmd, progressCallback=None, bufferSize=16384, outputLog=None):
    """ popen-like function, that accepts execvp-style arguments too (i.e. an
        array of params, thus making shell escaping unnecessary)

        cmd can be either a string (like "ls -l /dev"), or an array of
        arguments ["ls", "-l", "/dev"]

        Returns the command's error code, a stream with stdout's contents
        and a stream with stderr's contents

        progressCallback --> progress bar twiddler
        outputLog --> optional log file file object write method
    """
    cmd_is_list = type(cmd) in (types.ListType, types.TupleType)
    if cmd_is_list:
        cmd = map(str, cmd)
    c = subprocess.Popen(cmd, bufsize=0, stdin=subprocess.PIPE,
                stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                close_fds=True, shell=(not cmd_is_list))

    # We don't write to the child process
    c.stdin.close()

    # Create two temporary streams to hold the info from stdout and stderr
    child_out = tempfile.TemporaryFile(prefix = '/tmp/my-popen-', mode = 'r+b')
    child_err = tempfile.TemporaryFile(prefix = '/tmp/my-popen-', mode = 'r+b')

    # Map the input file descriptor with the temporary (output) one
    fd_mappings = [(c.stdout, child_out), (c.stderr, child_err)]
    exitcode = None
    count = 1

    while 1:
        # Is the child process done?
        status = c.poll()
        if status is not None:
            if status >= 0:
                # Save the exit code, we still have to read from the pipes
                exitcode = status
            else:
                # Some signal sent to this process
                if outputLog is not None:
                    outputLog("rhn_popen: Signal %s received\n" % (-status))
                exitcode = status
                break

        fd_set = map(lambda x: x[0], fd_mappings)
        readfds = select.select(fd_set, [], [])[0]

        for in_fd, out_fd in fd_mappings:
            if in_fd in readfds:
                # There was activity on this file descriptor
                output = os.read(in_fd.fileno(), bufferSize)
                if output:
                    # show progress
                    if progressCallback:
                        count = count + len(output)
                        progressCallback(count)

                    if outputLog is not None:
                        outputLog(output)

                    # write to the output buffer(s)
                    out_fd.write(output)
                    out_fd.flush()

        if exitcode is not None:
            # Child process is done
            break

    for f_in, f_out in fd_mappings:
        f_in.close()
        f_out.seek(0, 0)

    return exitcode, child_out, child_err
