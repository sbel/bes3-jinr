# $HeadURL$
"""
 Set of utilities to retrieve Information from proxy
"""
__RCSID__ = "568ee1a (2011-09-30 13:16:43 +0200) Adri Casajs <adria@ecm.ub.es>"
import base64
import types
import inspect
from DIRAC import S_OK, S_ERROR
from DIRAC.Core.Security.X509Chain import X509Chain, g_X509ChainType
from DIRAC.Core.Security.VOMS import VOMS
from DIRAC.Core.Security import Locations

__NOTIFIED_CALLERS = set()
stack = inspect.stack()
caller = ( stack[1][1], stack[1][2] )
if caller not in __NOTIFIED_CALLERS:
  print
  print 'From %s at line %s:' % caller
  print '[Deprecation warning] DIRAC.Core.Security.Misc will not be available in next release,'
  print '                      use DIRAC.Core.Security.ProxyInfo instead.'
  print
  __NOTIFIED_CALLERS.add( caller )


def getProxyInfo( proxy = False, disableVOMS = False ):
  """
  Returns a dict with all the proxy info
  * values that will be there always
   'chain' : chain object containing the proxy
   'subject' : subject of the proxy
   'issuer' : issuer of the proxy
   'isProxy' : bool
   'isLimitedProxy' : bool
   'validDN' : Valid DN in DIRAC
   'validGroup' : Valid Group in DIRAC
   'secondsLeft' : Seconds left
  * values that can be there
   'path' : path to the file,
   'group' : DIRAC group
   'groupProperties' : Properties that apply to the DIRAC Group
   'username' : DIRAC username
   'identity' : DN that generated the proxy
   'hostname' : DIRAC host nickname
   'VOMS'
  """
  #Discover proxy location
  proxyLocation = False
  if type( proxy ) == g_X509ChainType:
    chain = proxy
  else:
    if not proxy:
      proxyLocation = Locations.getProxyLocation()
    elif type( proxy ) in ( types.StringType, types.UnicodeType ):
      proxyLocation = proxy
    if not proxyLocation:
      return S_ERROR( "Can't find a valid proxy" )
    chain = X509Chain()
    retVal = chain.loadProxyFromFile( proxyLocation )
    if not retVal[ 'OK' ]:
      return S_ERROR( "Can't load %s: %s " % ( proxyLocation, retVal[ 'Message' ] ) )

  retVal = chain.getCredentials()
  if not retVal[ 'OK' ]:
    return retVal

  infoDict = retVal[ 'Value' ]
  infoDict[ 'chain' ] = chain
  if proxyLocation:
    infoDict[ 'path' ] = proxyLocation

  if not disableVOMS and chain.isVOMS()['Value']:
    infoDict[ 'hasVOMS' ] = True
    retVal = VOMS().getVOMSAttributes( chain )
    if retVal[ 'OK' ]:
      infoDict[ 'VOMS' ] = retVal[ 'Value' ]
    else:
      infoDict[ 'VOMSError' ] = retVal[ 'Message' ].strip()

  return S_OK( infoDict )

def getProxyInfoAsString( proxyLoc = False, disableVOMS = False ):
  """
    return the info as a printable string
  """
  retVal = getProxyInfo( proxyLoc, disableVOMS )
  if not retVal[ 'OK' ]:
    return retVal
  infoDict = retVal[ 'Value' ]
  return S_OK( formatProxyInfoAsString( infoDict ) )

def formatProxyInfoAsString( infoDict ):
  """
    convert a proxy infoDict into a string
  """
  leftAlign = 13
  contentList = []
  for field in ( 'subject', 'issuer', 'identity', ( 'secondsLeft', 'timeleft' ),
                 ( 'group', 'DIRAC group' ), 'path', 'username',
                 ( 'hasVOMS', 'VOMS' ), ( 'VOMS', 'VOMS fqan' ), ( 'VOMSError', 'VOMS Error' ) ):
    if type( field ) == types.StringType:
      dispField = field
    else:
      dispField = field[1]
      field = field[0]
    if not field in infoDict:
      continue
    if field == 'secondsLeft':
      secs = infoDict[ field ]
      hours = int( secs / 3600 )
      secs -= hours * 3600
      mins = int( secs / 60 )
      secs -= mins * 60
      value = "%02d:%02d:%02d" % ( hours, mins, secs )
    else:
      value = infoDict[ field ]
    contentList.append( "%s: %s" % ( dispField.ljust( leftAlign ), value ) )
  return "\n".join( contentList )


def getProxyStepsInfo( chain ):
  """
   Extended information of all Steps in the ProxyChain
   Returns a list of dictionary with Info for each Step.
  """
  infoList = []
  nC = chain.getNumCertsInChain()['Value']
  for i in range( nC ):
    cert = chain.getCertInChain( i )['Value']
    stepInfo = {}
    stepInfo[ 'subject' ] = cert.getSubjectDN()['Value']
    stepInfo[ 'issuer' ] = cert.getIssuerDN()['Value']
    stepInfo[ 'serial' ] = cert.getSerialNumber()['Value']
    stepInfo[ 'not before' ] = cert.getNotBeforeDate()['Value']
    stepInfo[ 'not after' ] = cert.getNotAfterDate()['Value']
    stepInfo[ 'lifetime' ] = cert.getRemainingSecs()['Value']
    stepInfo[ 'extensions' ] = cert.getExtensions()[ 'Value' ]
    dG = cert.getDIRACGroup( ignoreDefault = True )['Value']
    if dG:
      stepInfo[ 'group' ] = dG
    if cert.hasVOMSExtensions()[ 'Value' ]:
      stepInfo[ 'VOMS ext' ] = True
    infoList.append( stepInfo )
  return S_OK( infoList )

def formatProxyStepsInfoAsString( infoList ):
  """
  Format the List of Proxy steps dictionaries as a printable string.
  """
  contentsList = []
  for i in range( len( infoList ) ):
    contentsList.append( " + Step %s" % i )
    stepInfo = infoList[i]
    for key in ( 'subject', 'issuer', 'serial', 'not after', 'not before',
                 'group', 'VOMS ext', 'lifetime', 'extensions' ):
      if key in stepInfo:
        value = stepInfo[ key ]
        if key == 'serial':
          value = base64.b16encode( value )
        if key == 'lifetime':
          secs = value
          hours = int( secs / 3600 )
          secs -= hours * 3600
          mins = int( secs / 60 )
          secs -= mins * 60
          value = "%02d:%02d:%02d" % ( hours, mins, secs )
        if key == "extensions":
          value = "\n   %s" % "\n   ".join( [ "%s = %s" % ( extName.strip().rjust( 20 ), extValue.strip() )
                                              for extName, extValue in value ] )
        contentsList.append( "  %s : %s" % ( key.ljust( 10 ).capitalize(), value ) )
  return "\n".join( contentsList )
