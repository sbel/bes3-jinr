#!/usr/bin/env python
########################################################################
# $HeadURL$
# File :   dirac-start-component
# Author : Ricardo Graciani
########################################################################
"""
Start DIRAC component using runsvctrl utility
"""
__RCSID__ = "ba520bb (2010-11-29 14:59:42 +0000) Ricardo Graciani <graciani@ecm.ub.es>"
#
from DIRAC.Core.Base import Script
Script.disableCS()
Script.setUsageMessage( '\n'.join( [ __doc__.split( '\n' )[1],
                                     'Usage:',
                                     '  %s [option|cfgfile] ... [system [service|agent]]' % Script.scriptName,
                                     'Arguments:',
                                     '  system:        Name of the system for the component (default *: all)',
                                     '  service|agent: Name of the particular component (default *: all)' ] ) )
Script.parseCommandLine()
args = Script.getPositionalArgs()
if len( args ) > 2:
  Script.showHelp()
  exit( -1 )

system = '*'
component = '*'
if len( args ) > 0:
  system = args[0]
if system != '*':
  if len( args ) > 1:
    component = args[1]
#
from DIRAC.Core.Utilities import InstallTools
#
InstallTools.exitOnError = True
#
result = InstallTools.runsvctrlComponent( system, component, 'u' )
if not result['OK']:
  print 'ERROR:', result['Message']
  exit( -1 )

InstallTools.printStartupStatus( result['Value'] )
