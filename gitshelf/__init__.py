# Copyright 2012 Hewlett-Packard Development Company, L.P. All Rights Reserved.
#
# Author: Simon McCartney <simon.mccartney@hp.com>
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.
import logging
import os
import errno
from sh import git
from gitshelf.utils import Url

LOG = logging.getLogger(__name__)


class Book:
    """ Object to represent a book - repo on disk

        Books can be one of 2 types:
            1) a git repo
            2) a symlink to another location

        Keyword arguments:
            path -- absolute or relative path to the location the repo should be in
            git -- git url to be used as the source for the repo
            branch -- branch/sha1/tag to be used in the checkout, defaults to master
            link -- destination of the link target
            skiprepourlcheck -- flag to skip that the git url matches the definition during status checks
            fakeroot -- a gitshelf may specify absolute paths, setting fakeroot allows you to make an absolute path relative to the passed path

    """

    def __init__(self,
                 book,
                 git=None,
                 branch='master',
                 link=None,
                 skiprepourlcheck=False,
                 fakeroot=None):
        """Instantiate a book object"""
        self.path = book
        self.git = git
        self.link = link
        self.branch = branch
        self.skiprepourlcheck = skiprepourlcheck
        self.fakeroot = fakeroot

        if (self.git is None) and (self.link is None):
            raise StandardError("Book is neither git or link!")

        if self.fakeroot is not None:
            LOG.debug('fakepath set, prepending {0} to {1}'.format(
                self.fakeroot, self.path))
            # need to strip any leading os.sep
            book_path = os.path.join(self.fakeroot, self.path.lstrip(os.sep))
            self.path = book_path
            LOG.debug('book.path is now {0}'.format(self.path))

    def create(self):
        if self.git and self.link is None:
            self._create_git()
        elif self.link and self.git is None:
            self._create_link()

    def _create_git(self):
        """create a book from a git repo"""

        if not os.path.exists(self.path):
            LOG.info(("Creating book {0} from {1}, branch: {2}" +
                     "").format(self.path, self.git, self.branch))
            git.clone(self.git, self.path)
        else:
            LOG.info("Book {0} already exists".format(self.path))

        cwd = os.getcwd()
        os.chdir(self.path)

        if self.skiprepourlcheck:
            remote_match_found = False
            for remote in git("remote", "-v"):
                remote_parts = remote.split()

                if Url(remote_parts[1]) == Url(self.git):
                    remote_match_found = True

            if remote_match_found:
                LOG.debug('Found {0} in the list of remotes for {1}'.format(self.git, self.path))
            else:
                LOG.error('ERROR: {0} wasn\'t found in the list of remotes for {1}'.format(self.git, self.path))

        # check the branch is set as we expect
        # cb = git("symbolic-ref", "HEAD").replace('refs/heads/', '').rstrip('\r\n')
        cb = git('describe', '--all', '--contains', '--abbrev=4', 'HEAD').rstrip('\r\n')
        sha1 = git('rev-parse', 'HEAD').rstrip('\r\n')
        LOG.warn("Book {0}'s current branch is {1}".format(self.path, cb))
        LOG.warn("Book {0}'s current sha1 is {1}".format(self.path, sha1))

        if ((cb != self.branch) or (sha1 != self.branch)):
            LOG.info("Switching {0} from {1} to branch {2}".format(self.path,
                                                                   cb,
                                                                   self.branch))
            git.fetch
            git.checkout(self.branch)

        os.chdir(cwd)

    def _create_link(self):
        """create a book from a link to somewhere else"""

        if not os.path.islink(self.path):
            LOG.info("Creating book {0} via a link to {1}".format(self.path, self.link))
            # create the parent directory, if required
            self._mkdir_p(os.path.dirname(self.path.rstrip(os.sep)))
            # create the symlink
            os.symlink(self.link, self.path)
        else:
            LOG.info("Book {0} already exists, target: {1}".format(self.path, os.readlink(self.path)))

    def _mkdir_p(self, path):
        try:
            os.makedirs(path)
        except OSError as exc:  # Python >2.5
            if exc.errno == errno.EEXIST and os.path.isdir(path):
                pass
            else:
                raise

    def status(self):
        if self.git and self.link is None:
            # git repo, check it exists & isn't dirty
            if not os.path.exists(self.path):
                LOG.info("ERROR book {0} from {1} doesn't exist.".format(
                    self.path,
                    self.git))
            else:
                # chdir to the book & run `git status`
                cwd = os.getcwd()
                os.chdir(self.path)
                LOG.info("# book {0}".format(self.path))
                LOG.info(git.status())
                os.chdir(cwd)
        elif self.link and self.git is None:
            # check the link points to the correct location
            link_target = os.readlink(self.path)
            LOG.debug('book: {0} should point to {1}, it points to {2}'.format(self.path, self.link, link_target))
            if link_target == self.link:
                LOG.info('# book {0} correctly points to {1}'.format(self.path, self.link))
            else:
                LOG.error('{0} should point to {1}, it points to {2}'.format(self.path, self.link, self.link))
        else:
            LOG.error('Unknown book type: {0}'.format(self.path))
