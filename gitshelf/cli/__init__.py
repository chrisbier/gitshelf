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
import yaml
import os
from sh import git
from cliff.command import Command

LOG = logging.getLogger(__name__)


class BaseCommand(Command):
    """ Parent Command object for gitshelf """

    def get_parser(self, prog_name):
        parser = super(BaseCommand, self).get_parser(prog_name)

        parser.add_argument('--gitshelf',
                            dest='gitshelf',
                            default='gitshelf.yml',
                            nargs=1,
                            help="path to gitshelf YAML config, defaults to gitshelf.yml",
                            action='store')

        parser.add_argument('--skip-deletes', help="skip and group/rule deletes", action="store_true")

        parser.add_argument('--fakeroot',
                            dest='fakeroot',
                            default=None,
                            nargs=1,
                            help='path to prepand to any book paths, to test shelves ' \
                                    'that are absolute without using the absolute path')

        parser.add_argument('--dry-run',
                            default=False,
                            help="Defaults to False",
                            action='store_true')

        return parser

    def post_execute(self, data):
        """ Format the results locally if needed.

        By default we just return data.

        :param data: Whatever is returned by self.execute()

        """
        return data

    def take_action(self, parsed_args):
        # TODO: Common Exception Handling Here
        results = self.execute(parsed_args)
        return self.post_execute(results)

    def _parse_configuration(self, parsed_args):
        # Read the main config file
        LOG.debug(parsed_args)
        config_file = parsed_args.gitshelf.pop() if isinstance(parsed_args.gitshelf, list) else parsed_args.gitshelf
        LOG.debug("config_file = {0}".format(config_file))

        with open(config_file) as fh:
            config = yaml.load(fh)

        LOG.debug(config)

        return config