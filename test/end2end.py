#
# Copyright 2012-2016 Ghent University
#
# This file is part of vsc-mympirun,
# originally created by the HPC team of Ghent University (http://ugent.be/hpc/en),
# with support of Ghent University (http://ugent.be/hpc),
# the Flemish Supercomputer Centre (VSC) (https://www.vscentrum.be),
# the Flemish Research Foundation (FWO) (http://www.fwo.be/en)
# and the Department of Economy, Science and Innovation (EWI) (http://www.ewi-vlaanderen.be/en).
#
# https://github.com/hpcugent/vsc-mympirun
#
# vsc-mympirun is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation v2.
#
# vsc-mympirun is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with vsc-mympirun.  If not, see <http://www.gnu.org/licenses/>.
#
"""
End-to-end tests for mympirun (with mocking of real 'mpirun' command).

@author: Jeroen De Clerck (HPC-UGent)
@author: Kenneth Hoste (HPC-UGent)
@author: Caroline De Brouwer (HPC-UGent)
"""
import copy
import os
import re
import shutil
import stat
import tempfile
import unittest
from vsc.utils.run import run_simple


FAKE_MPIRUN = """#!/bin/bash
echo 'fake mpirun'
echo $@
"""

def install_fake_mpirun(cmdname, path):
    """Install fake mpirun command with given name in specified location"""
    fake_mpirun = os.path.join(path, cmdname)
    open(fake_mpirun, 'w').write(FAKE_MPIRUN)
    os.chmod(fake_mpirun, stat.S_IRUSR|stat.S_IXUSR)
    os.environ['PATH'] = '%s:%s' % (path, os.getenv('PATH', ''))


class TestEnd2End(unittest.TestCase):
    """End-to-end tests for mympirun"""

    def setUp(self):
        """Prepare to run test."""
        self.orig_environ = copy.deepcopy(os.environ)

        # add /bin to $PATH, /lib to $PYTHONPATH
        topdir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        os.environ['PATH'] = '%s:%s' % (os.path.join(topdir, 'bin'), os.getenv('PATH', ''))
        os.environ['PYTHONPATH'] = '%s:%s' % (os.path.join(topdir, 'lib'), os.getenv('PYTHONPATH', ''))

        self.tmpdir = tempfile.mkdtemp()

        # make sure we're using the right mympirun installation...
        ec, out = run_simple("python -c 'import vsc.mympirun; print vsc.mympirun.__file__'")
        expected_path = os.path.join(topdir, 'lib', 'vsc', 'mympirun')
        self.assertTrue(os.path.samefile(os.path.dirname(out.strip()), expected_path))

    def tearDown(self):
        """Clean up after running test."""
        os.environ = self.orig_environ
        shutil.rmtree(self.tmpdir)

    def test_serial(self):
        """Test running of a serial command via mympirun."""
        print os.environ['PATH']

        install_fake_mpirun('mpirun', self.tmpdir)
        ec, out = run_simple("mympirun.py --setmpi impirun hostname")
        self.assertEqual(ec, 0)
        self.assertTrue(out.strip().endswith('hostname'))

    def test_sched(self):
        """ Test --sched(type) option """
        install_fake_mpirun('mpirun', self.tmpdir)
        mpi_set = ['impirun', 'ompirun']
        mpi_out = [
            # local, cluster
            ['-genv I_MPI_DEVICE shm', "-genv I_MPI_FABRICS 'shm:dapl'"],
            ['--mca btl sm,self', "--mca btl 'sm,openib,self'"],
        ]

        for i in range(0, len(mpi_set)):
            ec, out = run_simple("mympirun.py --setmpi %s --sched local hostname" % mpi_set[i])
            self.assertEqual(ec, 0)
            self.assertTrue(out.strip().endswith('hostname'))
            self.assertTrue(any(n in out for n in mpi_out[i]))