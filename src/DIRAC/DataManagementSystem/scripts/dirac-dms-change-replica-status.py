#! /usr/bin/env python
########################################################################
# $HeadURL$
########################################################################
__RCSID__   = "02424f4 (2012-03-21 17:26:24 +0100) Andrei Tsaregorodtsev <atsareg@gmail.com>"

from DIRAC.Core.Base import Script 

Script.setUsageMessage("""
Change status of replica of a given file or a list of files at a given Storage Element 

Usage:
   %s <lfn | fileContainingLfns> <SE> <status>
""" % Script.scriptName)

Script.parseCommandLine()

from DIRAC.DataManagementSystem.Client.ReplicaManager import CatalogInterface
catalog = CatalogInterface()
import sys,os

if not len(sys.argv) == 4:
  Script.showHelp()
  DIRAC.exit( -1 )
else:
  inputFileName = sys.argv[1]
  se = sys.argv[2]
  newStatus = sys.argv[3]

if os.path.exists(inputFileName):
  inputFile = open(inputFileName,'r')
  string = inputFile.read()
  lfns = string.splitlines()
  inputFile.close()
else:
  lfns = [inputFileName]

res = catalog.getCatalogReplicas(lfns,True)
if not res['OK']:
  print res['Message']
  sys.exit()
replicas = res['Value']['Successful']

lfnDict = {}
for lfn in lfns:
  lfnDict[lfn] = {}
  lfnDict[lfn]['SE'] = se
  lfnDict[lfn]['Status'] = newStatus
  lfnDict[lfn]['PFN'] = replicas[lfn][se]

res = catalog.setCatalogReplicaStatus(lfnDict)
if not res['OK']:
  print "ERROR:",res['Message']
if res['Value']['Failed']:
  print "Failed to update %d replica status" % len(res['Value']['Failed'])
if res['Value']['Successful']:
  print "Successfully updated %d replica status" % len(res['Value']['Successful'])
