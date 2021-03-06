# cfbda43 (2010-02-21 22:05:44 +0000) Ricardo Graciani <graciani@ecm.ub.es>

"""
    Workflow Utility module contains a number of functions useful for various
    workflow operations
"""

__RCSID__ = "$Revision: 1.3 $"

import types, re

def getSubstitute(param,skip_list=[]):
  """ Get the variable name to which the given parameter is referring
  """
  result = []
  resList = re.findall("@{([][\w,.:$()]+)}",str(param))
  if resList:
    for match in resList:
      if match not in skip_list:
        result.append(match)

  return result

def substitute(param,variable,value):
  """ Substitute the variable reference with the value
  """

  tmp_string = str(param).replace('@{'+variable+'}',value)
  if type(param) in types.StringTypes:
    return tmp_string
  else:
    return eval(tmp_string)

def resolveVariables(varDict):
  """ Resolve variables defined in terms of others within the same dictionary
  """
  max_tries = 10
  variables = varDict.keys()
  ntry = 0
  while ntry < max_tries:
    substFlag = False
    for var,value in varDict.items():
      if type(value) in types.StringTypes:
        substitute_vars = getSubstitute(value)
        for substitute_var in substitute_vars:
          if substitute_var in variables:
            varDict[var] = substitute(varDict[var],substitute_var,varDict[substitute_var])
            substFlag = True
    if not substFlag:
      break
    ntry += 1
  else:
    print "Failed to resolve referencies in %d attempts" % max_tries

def dataFromOption(parameter):

  result = []

  if parameter.type.lower() == 'option':

    fields = parameter.value.split(',')

    for f in fields:
      if ( re.search('FILE\s*=',f ) ) :
        #print f
        fname = re.search("FILE\s*=\s*'([][;\/\w.:\s@{}-]+)'",f).group(1)
        res = re.search("TYP\w*\s*=\s*'(\w+)'",f)
        if res:
          ftype = res.group(1)
        else:
          ftype = "Unknown"

        result.append((fname,ftype))

  return result

def expandDatafileOption(option):

  result = ''

  if not re.search(';;',option.value):
    return result

  files = dataFromOption(option)
  if len(files) == 1:
    fname,ftype = files[0]
    fnames = fname.split(';;')
    if len(fnames) > 1:

      template = option.value.strip().replace('=','',1)
      template = template.replace('{','')
      template = template.replace('}','')
      opt = []
      for f in fnames:
        opt.append(template.replace(fname,f))

      result = '={'+','.join(opt)+'}'

  return result

#def dataFromOptions(parameters):
#
#  for n,v in parameters.items():
#    files = dataFromOption(v)
#    if fname:
#      gLogger.info( str( files ) )
