########################################################################
# $HeadURL$
########################################################################

""" GraphData encapsulates input data for the DIRAC Graphs plots
    
    The DIRAC Graphs package is derived from the GraphTool plotting package of the
    CMS/Phedex Project by ... <to be added>
"""

__RCSID__ = "d9b4e3b (2012-04-09 22:32:00 +0200) Andrei Tsaregorodtsev <atsareg@gmail.com>"

import types, datetime, numpy, time
from DIRAC.Core.Utilities.Graphs.GraphUtilities import convert_to_datetime, to_timestamp, pretty_float
from matplotlib.dates import date2num

DEBUG = 0

def get_key_type( keys ):
  """ A utility function to guess the type of the plot keys
  """

  min_time_stamp = 1000000000
  max_time_stamp = 1900000000
  time_type = True
  num_type = True
  string_type = True
  key_type = 'unknown'
  for key in keys:
    if time_type:
      try:
        time_data = to_timestamp( key )
        if time_data < min_time_stamp or time_data > max_time_stamp:
          time_type = False
      except ValueError:
        time_type = False
    if num_type:
      try:
        num_data = float( key )
      except:
        num_type = False
    if type( key ) not in types.StringTypes:
      string_type = False

  # Take the most restrictive type
  if string_type:
    key_type = "string"
  if num_type :
    key_type = "numeric"
  if time_type:
    key_type = "time"

  return key_type

class GraphData:

  def __init__( self, data = {} ):

    self.truncated = 0
    self.all_keys = []
    self.labels = []
    self.label_values = []
    self.subplots = {}
    self.plotdata = None
    self.data = dict( data )
    self.key_type = 'string'
    self.initialize()

  def isEmpty( self ):
    """ Check if there is no data inserted
    """

    return not self.plotdata and not self.subplots

  def setData( self, data ):
    """ Add data to the GraphData object
    """

    self.data = dict( data )
    self.initialize()

  def initialize( self, key_type = None ):

    keys = self.data.keys()
    if not keys:
      print "GraphData Error: empty data"
    start = time.time()

    if type( self.data[keys[0]] ) == types.DictType:
      for key in self.data:
        self.subplots[key] = PlotData( self.data[key], key_type = key_type )
    else:
      self.plotdata = PlotData( self.data, key_type = key_type )

    if DEBUG:
      print "Time: plot data", time.time() - start, len( self.subplots )

    if self.plotdata:
      self.all_keys = self.plotdata.getKeys()
    else:
      tmpset = set()
      for sub in self.subplots.values():
        for key in sub.getKeys():
          tmpset.add( key )
      self.all_keys = list( tmpset )

    if key_type:
      self.key_type = key_type
    else:
      self.key_type = get_key_type( self.all_keys )
    self.sortKeys()
    self.makeNumKeys()

    self.sortLabels()

  def expandKeys( self ):

    if not self.plotdata:
      for sub in self.subplots:
        self.subplots[sub].expandKeys( self.all_keys )

  def isSimplePlot( self ):

    return not self.plotdata is None

  def sortLabels( self, sort_type = 'max_value' ):
    """ Sort labels with a specified method:
          alpha - alphabetic order
          max_value - by max value of the subplot
          sum - by the sum of values of the subplot
          last_value - by the last value in the subplot
    """
    if self.plotdata:
      if self.key_type == "string":
        if sort_type in ['max_value', 'sum']:
          self.labels = self.plotdata.sortKeys( 'weight' )
        else:
          self.labels = self.plotdata.sortKeys()
        self.label_values = [ self.plotdata.parsed_data[l] for l in self.labels]

    else:
      if sort_type == 'max_value':
        pairs = zip( self.subplots.keys(), self.subplots.values() )
        pairs.sort( key = lambda x: x[1].max_value, reverse = True )
        self.labels = [ x[0] for x in pairs ]
        self.label_values = [ x[1].max_value for x in pairs ]
      elif sort_type == 'last_value':
        pairs = zip( self.subplots.keys(), self.subplots.values() )
        pairs.sort( key = lambda x: x[1].last_value, reverse = True )
        self.labels = [ x[0] for x in pairs ]
        self.label_values = [ x[1].last_value for x in pairs ]
      elif sort_type == 'sum':
        pairs = []
        for key in self.subplots:
          pairs.append( ( key, self.subplots[key].sum_value ) )
        pairs.sort( key = lambda x: x[1], reverse = True )
        self.labels = [ x[0] for x in pairs ]
        self.label_values = [ x[1] for x in pairs ]
      elif sort_type == 'alpha':
        self.labels = self.subplots.keys()
        self.labels.sort()
        self.label_values = [ self.subplots[x].sum_value for x in self.labels ]
      else:
        self.labels = self.subplots.keys()

  def sortKeys( self ):
    """ Sort the graph keys in a natural order
    """

    if self.plotdata:
      self.plotdata.sortKeys()
      self.all_keys = self.plotdata.getKeys()
    else:
      self.all_keys.sort()

    self.min_key = min( self.all_keys )
    self.max_key = max( self.all_keys )

  def makeNumKeys( self ):
    """ Make numerical representation of the graph keys suitable for plotting
    """

    self.all_num_keys = []
    if self.key_type == "string":
      self.all_string_map = {}
      next = 0
      for key in self.all_keys:
        self.all_string_map[key] = next
        self.all_num_keys.append( next )
        next += 1
    elif self.key_type == "time":
      self.all_num_keys = [ date2num( datetime.datetime.fromtimestamp( to_timestamp( key ) ) ) for key in self.all_keys ]
    elif self.key_type == "numeric":
      self.all_num_keys = [ float( key ) for key in self.all_keys ]

    self.min_num_key = min( self.all_num_keys )
    self.max_num_key = max( self.all_num_keys )

  def makeCumulativeGraph( self ):
    """ Prepare data for the cumulative graph
    """

    self.expandKeys()

    if self.plotdata:
      self.plotdata.makeCumulativePlot()
    if self.truncated:
      self.otherPlot.makeCumulativePlot()
    if self.subplots:
      for label in self.subplots:
        self.subplots[label].makeCumulativePlot()

    self.sortLabels( sort_type = 'last_value' )

  def getLabels( self ):
    """ Get the graph labels together with the numeric values used for the label 
        sorting
    """

    labels = []
    if self.plotdata:
      if self.key_type != 'string':
        labels = [( 'NoLabels', 0. )]
      else:
        labels = zip( self.labels, self.label_values )

    elif self.truncated:
      tlabels = self.labels[:self.truncated]
      tvalues = self.label_values[:self.truncated]
      labels = zip( tlabels, tvalues )
      labels.append( ( 'Others', sum( self.label_values[self.truncated:] ) ) )
    else:
      labels = zip( self.labels, self.label_values )

    return labels

  def getStringMap( self ):
    """ Get string to number mapping for numeric type keys
    """
    return self.all_string_map

  def getNumberOfKeys( self ):

    return len( self.all_keys )

  def getNumberOfLabels( self ):

    if self.truncated:
      return self.truncated + 1
    else:
      return len( self.labels )

  def getPlotNumData( self, label = None, zipFlag = True ):
    """ Get the plot data in a numeric form
    """

    if self.plotdata:
      if zipFlag:
        return zip( self.plotdata.getNumKeys(), self.plotdata.getValues() )
      else:
        return self.plotdata.getValues()
    elif label is not None:
      if label == "Others":
        return self.otherPlot.getPlotDataForNumKeys( self.all_num_keys )
      else:
        return self.subplots[label].getPlotDataForNumKeys( self.all_num_keys )
    else:
      # Get the sum of all the subplots
      self.expandKeys()
      arrays = []
      for label in self.subplots:
        arrays.append( numpy.array( [ x[1] for x in self.subplots[label].getPlotDataForNumKeys( self.all_num_keys, True )] ) )
      sum_array = sum( arrays )
      if zipFlag:
        return zip( self.all_num_keys, list( sum_array ) )
      else:
        return sum_array

  def truncateLabels( self, limit = 10 ):
    """ Truncate the number of labels to the limit, leave the most important
        ones, accumulate the rest in the 'Others' label 
    """

    if self.plotdata:
      return
    nLabels = len( self.labels )
    if nLabels <= limit:
      return

    self.truncated = limit

    new_labels = self.labels[:limit]
    new_labels.append( 'Others' )

    other_data = {}
    for key in self.all_keys:
      other_data[key] = 0.
    for label in self.labels:
      if label not in new_labels:
        for key in self.all_keys:
          if self.subplots[label].parsed_data.has_key( key ):
            other_data[key] += self.subplots[label].parsed_data[key]
    self.otherPlot = PlotData( other_data )

  def getStats( self ):
    """ Get statistics of the graph data
    """

    numData = self.getPlotNumData( zipFlag = False )
    if not len( numData ):
      return 0, 0, 0, 0

    numData = numpy.array( numData )
    min_value = numData.min()
    max_value = numData.max()
    average = float( numData.sum() ) / len( numData )
    current = numData[-1]
    return min_value, max_value, average, current

  def getStatString( self, unit = None ):
    """  Get a string summarizing the graph data statistics
    """
    min_value, max_value, average, current = self.getStats()
    tmpList = []
    unitString = ''
    if unit:
      unitString = str( unit )
    if max_value:
      try:
        s = "Max: " + pretty_float( max_value ) + " " + unitString
        tmpList.append( s.strip() )
      except Exception, e:
        pass
    if min_value:
      try:
        s = "Min: " + pretty_float( min_value ) + " " + unitString
        tmpList.append( s.strip() )
      except Exception, e:
        pass
    if average:
      try:
        s = "Average: " + pretty_float( average ) + " " + unitString
        tmpList.append( s.strip() )
      except Exception, e:
        pass
    if current:
      try:
        s = "Current: " + pretty_float( current ) + " " + unitString
        tmpList.append( s.strip() )
      except Exception, e:
        pass

    resultString = ', '.join( tmpList )
    return resultString


class PlotData:
  """ PlotData class is a container for a one dimensional plot data
  """

  def __init__( self, data, single = True, key_type = None ):

    self.key_type = "unknown"
    keys = data.keys()
    if not keys:
      print "PlotData Error: empty data"
      return

    # Original data
    self.data = dict( data )

    # Working copy of the parsed data  
    self.parsed_data = {}

    # Keys and values as synchronized lists
    self.keys = []
    self.num_keys = []
    self.values = []
    self.sorted_keys = []

    # Do initial data parsing
    self.parseData( key_type )
    if single:
      self.initialize()

  def initialize( self ):

    if self.key_type == "string":
      self.keys = self.sortKeys( 'weight' )
    else:
      self.keys = self.sortKeys()

    self.values = [ self.parsed_data[k] for k in self.keys ]
    values_to_sum = [ self.parsed_data[k] for k in self.keys if k != '' ]

    self.real_values = []
    for k in self.keys:
      if self.parsed_data[k] is not None:
        self.real_values.append( self.parsed_data[k] )

    self.values_sum = float( sum( self.real_values ) )

    # Prepare numerical representation of keys for plotting
    self.num_keys = []
    if self.key_type == "string":
      self.string_map = {}
      next = 0
      for key in self.keys:
        self.string_map[key] = next
        self.num_keys.append( next )
        next += 1
    elif self.key_type == "time":
      self.num_keys = [ date2num( datetime.datetime.fromtimestamp( to_timestamp( key ) ) ) for key in self.keys ]
    elif self.key_type == "numeric":
      self.num_keys = [ float( key ) for key in self.keys ]


    self.min_value = float( min( self.real_values ) )
    self.max_value = float( max( self.real_values ) )
    self.min_key = self.keys[0]
    self.max_key = self.keys[-1]
    self.sum_value = float( sum( self.real_values ) )
    self.last_value = float( self.real_values[-1] )

  def expandKeys( self, all_keys ):
    """ Fill zero values into the missing keys 
    """

    for k in all_keys:
      if not self.parsed_data.has_key( k ):
        self.parsed_data[k] = 0.

    self.sorted_keys = []
    self.keys = self.parsed_data.keys()
    self.initialize()

  def sortKeys( self, sort_type = 'alpha' ):
    """ Sort keys according to the specified method :
        alpha - sort in alphabetic order
        weight - sort in the order of values
    """

    if self.sorted_keys:
      return self.sorted_keys
    if sort_type == 'weight':
      pairs = zip( self.parsed_data.keys(), self.parsed_data.values() )
      pairs.sort( key = lambda x: x[1], reverse = True )
      self.sorted_keys = [ x[0] for x in pairs ]
    elif sort_type == 'alpha':
      self.sorted_keys = self.keys
      self.sorted_keys.sort()
    else:
      print "Unknown sorting type:", sort_type

    return self.sorted_keys

  def __data_size( self, item ):
    """
    Determine a numerical size for the data; this is used to
    sort the keys of the graph.

    If the item is a tuple, take the absolute value of the first entry.
    Otherwise, attempt to take the absolute value of that item.  If that
    fails, just return -1.
    """
    if type( item ) == types.TupleType:
      return abs( item[0] )
    try:
      return abs( item )
    except TypeError, te:
      return - 1

  def parseKey( self, key ):
    """
    Parse the name of the pivot; this is the identity function.
    """

    if self.key_type == "time":
      return to_timestamp( key )
    else:
      return key

  def parseDatum( self, data ):
    """
    Parse the specific data value; this is the identity.
    """
    try:
      result = float( data )
    except:
      result = None
    return result

  def parseData( self, key_type = None ):
    """
    Parse all the data values passed to the graph.  For this super class,
    basically does nothing except loop through all the data.  A sub-class
    should override the parseDatum and parse_pivot functions rather than
    this one.
    """
    if key_type:
      self.key_type = key_type
    else:
      self.key_type = get_key_type( self.data.keys() )
    new_parsed_data = {}
    for key, data in self.data.items():
      new_key = self.parseKey( key )
      data = self.parseDatum( data )
      #if data != None:
      new_parsed_data[ new_key ] = data
    self.parsed_data = new_parsed_data

    self.keys = self.parsed_data.keys()

  def makeCumulativePlot( self ):

    if not self.sorted_keys:
      self.sortKeys()

    cum_values = []
    if self.values[0] is None:
      cum_values.append( 0. )
    else:
      cum_values.append( self.values[0] )
    for i in range( 1, len( self.values ) ):
      if self.values[i] is None:
        cum_values.append( cum_values[i - 1] )
      else:
        cum_values.append( cum_values[i - 1] + self.values[i] )

    self.values = cum_values
    self.last_value = float( self.values[-1] )

  def getPlotData( self ):

    return self.parsed_data

  def getPlotNumData( self ):

    return zip( self.num_keys, self.values )

  def getPlotDataForKeys( self, keys ):

    result_pairs = []
    for key in keys:
      if self.parsed_data.has_key( key ):
        result_pairs.append( key, self.parsed_data[key] )
      else:
        result_pairs.append( key, None )

    return result_pairs

  def getPlotDataForNumKeys( self, num_keys, zeroes = False ):

    result_pairs = []
    for num_key in num_keys:
      try:
        ind = self.num_keys.index( num_key )
        if self.values[ind] is None and zeroes:
          result_pairs.append( ( self.num_keys[ind], 0. ) )
        else:
          result_pairs.append( ( self.num_keys[ind], self.values[ind] ) )
      except ValueError:
        if zeroes:
          result_pairs.append( ( num_key, 0. ) )
        else:
          result_pairs.append( ( num_key, None ) )

    return result_pairs

  def getKeys( self ):

    return self.keys

  def getNumKeys( self ):

    return self.num_keys

  def getValues( self ):

    return self.values

  def getMaxValue( self ):

    return max( self.values )

  def getMinValue( self ):

    return min( self.values )






