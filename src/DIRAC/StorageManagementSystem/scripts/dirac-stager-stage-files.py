#! /usr/bin/env python
########################################################################
# $HeadURL$
# File :    dirac-stager-stage-files
# Author :  Daniela Remenska
########################################################################
"""
- submit staging requests for a particular Storage Element! Default DIRAC JobID will be =0. 
  (not visible in the Job monitoring list though)

"""
__RCSID__ = "39d447e (2013-06-20 02:53:38 +0200) daniela <remenska@gmail.com>"
from DIRAC.Core.Base import Script
Script.setUsageMessage( '\n'.join( [ __doc__.split( '\n' )[1],
                                     'Usage:',
                                     '  %s SE FileName [...]' % Script.scriptName,
                                     'Arguments:',
                                     '  SE:       Name of Storage Element',
                                     '  FileName: LFN to Stage (or local file with list of LFNs)' ] ) )

Script.parseCommandLine( ignoreErrors = True )

args = Script.getPositionalArgs()

if len( args ) < 2:
  Script.showHelp()

seName = args[0]
fileName = args[1]

import os
import DIRAC
from DIRAC.Interfaces.API.Dirac import Dirac
from DIRAC.StorageManagementSystem.Client.StorageManagerClient import StorageManagerClient

stageLfns = {}

if os.path.exists( fileName ):
  try:
    lfnFile = open( fileName )
    lfns = [ k.strip() for k in lfnFile.readlines() ]
    lfnFile.close()
  except Exception:
    DIRAC.gLogger.exception( 'Can not open file', fileName )
    DIRAC.exit( -1 )
else:
  lfns = args[1:]

stageLfns[seName] = lfns
stagerClient = StorageManagerClient()

res = stagerClient.setRequest( stageLfns, 'WorkloadManagement',
                                      'updateJobFromStager@WorkloadManagement/JobStateUpdate',
                                      0 ) # fake JobID = 0
if not res['OK']:
  DIRAC.gLogger.error( res['Message'] )
  DIRAC.exit( -1 )
else:
  print "Stage request submitted for LFNs:\n %s" %lfns
  print "SE= %s" %seName
  print "You can check their status and progress with dirac-stager-monitor-file <LFN> <SE>"

'''Example1:
dirac-stager-stage-files.py GRIDKA-RDST filesToStage.txt 
Stage request submitted for LFNs:
 ['/lhcb/LHCb/Collision12/FULL.DST/00020846/0002/00020846_00023458_1.full.dst', '/lhcb/LHCb/Collision12/FULL.DST/00020846/0003/00020846_00032669_1.full.dst', '/lhcb/LHCb/Collision12/FULL.DST/00020846/0003/00020846_00032666_1.full.dst']
SE= GRIDKA-RDST
You can check their status and progress with dirac-stager-monitor-file <LFN> <SE>

Example2:
dirac-stager-stage-files.py GRIDKA-RDST /lhcb/LHCb/Collision12/FULL.DST/00020846/0003/00020846_00032641_1.full.dst
Stage request submitted for LFNs:
 ['/lhcb/LHCb/Collision12/FULL.DST/00020846/0003/00020846_00032641_1.full.dst']
SE= GRIDKA-RDST
You can check their status and progress with dirac-stager-monitor-file <LFN> <SE>
'''

DIRAC.exit()
