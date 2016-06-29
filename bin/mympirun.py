#!/usr/bin/env python
#
# Copyright 2009-2016 Ghent University
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
A mpirun wrapper

v1 bash 10/08/2009
v2 python rewrite 19/03/2010
v3 refactored python 28/08/2012
v4 cleanup 5/11/2013

Expert mode:
    export MYMPIRUN_MAIN_EXCEPTION=1 to show all exceptions

TODO:
    intel tuning code

@author: Stijn De Weirdt, Jens Timmerman (HPC UGent / VSC)
"""

import sys
import os
import traceback

from vsc.utils import fancylogger
from vsc.mympirun.rm.factory import getinstance
from vsc.mympirun.mpi.mpi import whatMPI
from vsc.mympirun.option import MympirunOption
from vsc.mympirun.rm.sched import whatSched

_logger = fancylogger.getLogger()
fancylogger.setLogLevelInfo()

class ExitException(Exception):
    """Exception thrown when we wish to exit, but no real errors occured"""
    _logger.info("ExitException was thrown: %s", Exception)


def get_mpi_and_sched_and_options():
    """Parses the mpi and scheduler based on current environment and guesses the best one to use

    returns:
    mpi             --
    sched           --
    mo              --
    """
    _logger.info("get_mpi_and_sched_and_options()")

    scriptname, mpi, found_mpi = whatMPI(sys.argv[0])
    _logger.info("whatMPI returned scriptname: %s, mpi: %s, found_mpi: %s" % (scriptname,mpi,found_mpi))

    ismpirun = scriptname == 'mpirun'

    mo = MympirunOption(ismpirun=ismpirun)

    if mo.args is None or len(mo.args) == 0:
        mo.parser.print_shorthelp()
        raise ExitException("Exit no args provided")

    sched, found_sched = whatSched(getattr(mo.options, 'schedtype', None))

    found_mpi_names = [x.__name__ for x in found_mpi]
    found_sched_names = [x.__name__ for x in found_sched]

    if mo.options.showmpi:
        fancylogger.setLogLevelInfo()
        _logger.info("Found MPI classes %s" % (", ".join(found_mpi_names)))
        raise ExitException("Exit from showmpi")

    if mo.options.showsched:
        fancylogger.setLogLevelInfo()
        _logger.info("Found Sched classes %s" % (", ".join(found_sched_names)))
        raise ExitException("Exit from showsched")

    if mpi is None:
        #mo.parser.print_shorthelp()
        mo.log.raiseException(("No MPI class found (scriptname %s; ismpirun %s). Please use mympirun through one "
                               "of the direct calls or make sure the mpirun command can be found. "
                               "Found MPI %s") % (scriptname, ismpirun, ", ".join(found_mpi_names)))
    else:
        mo.log.debug("Found MPI class %s (scriptname %s; ismpirun %s)" % (mpi.__name__, scriptname, ismpirun))

    if sched is None:
        mo.log.raiseException("No sched class found (options.schedtype %s ; found Sched classes %s)" %
                              (mo.options.schedtype, ", ".join(found_sched_names)))
    else:
        mo.log.debug("Found sched class %s from options.schedtype %s (all Sched found %s)" %
                     (sched.__name__, mo.options.schedtype, ", ".join(found_sched_names)))

    return mpi, sched, mo


def main():
    """Main function"""
    _logger.info("main()")

    try:
        m = getinstance(*get_mpi_and_sched_and_options())
        m.main()
        ec = 0
    except ExitException:
        ec = 0
    except Exception, e:
        _logger.info("Main failed")
        tb = traceback.format_exc()
        # # TODO: cleanup, only catch known exceptions
        if os.environ.get('MYMPIRUN_MAIN_EXCEPTION', 0) == '1':
            _logger.exception("Main failed")
        ec = 1
    finally:
        _logger.info("Trace: \n %s", tb)

    sys.exit(ec)

if __name__ == '__main__':
    main()
