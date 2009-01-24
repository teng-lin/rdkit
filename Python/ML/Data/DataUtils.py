## Automatically adapted for numpy.oldnumeric Jun 27, 2008 by -c

#
#  Copyright (C) 2000-2008  greg Landrum and Rational Discovery LLC
#   All Rights Reserved
#

""" Utilities for data manipulation

**FILE FORMATS:**

 - *.qdat files* contain quantized data suitable for
  feeding to learning algorithms.

  The .qdat file, written by _DecTreeGui_, is structured as follows:

   1) Any number of lines which are ignored.

   2) A line containing the string 'Variable Table'

      any number of variable definitions in the format:

      '# Variable_name [quant_bounds]'

        where '[quant_bounds]' is a list of the boundaries used for quantizing
         that variable.  If the variable is inherently integral (i.e. not
         quantized), this can be an empty list.

   3) A line beginning with '# ----' which signals the end of the variable list

   4) Any number of lines containing data points, in the format:

      'Name_of_point var1 var2 var3 .... varN'

      all variable values should be integers

   Throughout, it is assumed that varN is the result

 - *.dat files* contain the same information as .qdat files, but the variable
   values can be anything (floats, ints, strings).  **These files should
   still contain quant_bounds!**
   
 - *.qdat.pkl file* contain a pickled (binary) representation of
   the data read in.  They stores, in order:

    1) A python list of the variable names

    2) A python list of lists with the quantization bounds

    3) A python list of the point names
    
    4) A python list of lists with the data points

"""
from pyRDKit import RDConfig
from pyRDKit.utils import fileutils
from pyRDKit.ML.Data import MLData
from pyRDKit.Dbase.DbConnection import DbConnect
from pyRDKit.DataStructs import BitUtils
import string
import re,csv
import cPickle
import random

def permutation(nToDo):
  res = range(nToDo)
  random.shuffle(res)
  return res

def WriteData(outFile,varNames,qBounds,examples):
  """ writes out a .qdat file

    **Arguments**

      - outFile: a file object

      - varNames: a list of variable names

      - qBounds: the list of quantization bounds (should be the same length
         as _varNames_)

      - examples: the data to be written

  """
  outFile.write('# Quantized data from DataUtils\n')
  outFile.write('# ----------\n')
  outFile.write('# Variable Table\n')
  for i in xrange(len(varNames)):
    outFile.write('# %s %s\n'%(varNames[i],str(qBounds[i])))
  outFile.write('# ----------\n')
  for example in examples:
    outFile.write(string.join(map(str,example),' ')+'\n')
    

def ReadVars(inFile):
  """ reads the variables and quantization bounds from a .qdat or .dat file

    **Arguments**

      - inFile: a file object

    **Returns**

      a 2-tuple containing:

        1) varNames: a list of the variable names

        2) qbounds: the list of quantization bounds for each variable

  """
  varNames = []
  qBounds = []
  fileutils.MoveToMatchingLine(inFile,'Variable Table')
  inLine = inFile.readline()
  while string.find(inLine,'# ----') == -1:
    splitLine = string.split(inLine[2:],'[')
    varNames.append(string.strip(splitLine[0]))
    qBounds.append(splitLine[1][:-2])
    inLine = inFile.readline()
  for i in xrange(len(qBounds)):
    
    if qBounds[i] != '':
      l = string.split(qBounds[i],',')
      qBounds[i] = []
      for item in l:
        qBounds[i].append(float(item))
    else:
      qBounds[i] = []
  return varNames,qBounds

def ReadQuantExamples(inFile):
  """ reads the examples from a .qdat file

    **Arguments**

      - inFile: a file object

    **Returns**

      a 2-tuple containing:

        1) the names of the examples

        2) a list of lists containing the examples themselves

    **Note**

      because this is reading a .qdat file, it assumed that all variable values
      are integers
      
  """
  expr1 = re.compile(r'^#')
  expr2 = re.compile(r'[\ ]*|[\t]*')
  examples = []
  names = []
  inLine = inFile.readline()
  while inLine:
    if expr1.search(inLine) is None:
      resArr = expr2.split(inLine)
      if len(resArr)>1:
        examples.append(map(lambda x: int(x),resArr[1:]))
        names.append(resArr[0])
    inLine = inFile.readline()
  return names,examples

def ReadGeneralExamples(inFile):
  """ reads the examples from a .dat file

    **Arguments**

      - inFile: a file object

    **Returns**

      a 2-tuple containing:

        1) the names of the examples

        2) a list of lists containing the examples themselves

    **Note**

      - this attempts to convert variable values to ints, then floats.
        if those both fail, they are left as strings

  """
  expr1 = re.compile(r'^#')
  expr2 = re.compile(r'[\ ]*|[\t]*')
  examples = []
  names = []
  inLine = inFile.readline()
  while inLine:
    if expr1.search(inLine) is None:
      resArr = expr2.split(inLine)[:-1]
      if len(resArr)>1:
        for i in xrange(1,len(resArr)):
          d = resArr[i]
          try:
            resArr[i] = int(d)
          except ValueError:
            try:
              resArr[i] = float(d)
            except ValueError:
              pass
        examples.append(resArr[1:])
        names.append(resArr[0])
    inLine = inFile.readline()
  return names,examples

def BuildQuantDataSet(fileName):
  """ builds a data set from a .qdat file

    **Arguments**

      - fileName: the name of the .qdat file

    **Returns**

      an _MLData.MLQuantDataSet_
      
  """
  inFile = open(fileName,'r')

  varNames,qBounds = ReadVars(inFile)
  ptNames,examples = ReadQuantExamples(inFile)
  data = MLData.MLQuantDataSet(examples,qBounds=qBounds,varNames=varNames,
                               ptNames=ptNames)
  return data


def BuildDataSet(fileName):
  """ builds a data set from a .dat file

    **Arguments**

      - fileName: the name of the .dat file

    **Returns**

      an _MLData.MLDataSet_
      
  """
  inFile = open(fileName,'r')

  varNames,qBounds = ReadVars(inFile)
  ptNames,examples = ReadGeneralExamples(inFile)
  data = MLData.MLDataSet(examples,qBounds=qBounds,varNames=varNames,
                          ptNames=ptNames)
  return data


def CalcNPossibleUsingMap(data,order,qBounds,nQBounds=None):
  """ calculates the number of possible values for each variable in a data set

   **Arguments**

     - data: a list of examples

     - order: the ordering map between the variables in _data_ and _qBounds_

     - qBounds: the quantization bounds for the variables

   **Returns**

      a list with the number of possible values each variable takes on in the data set

   **Notes**

     - variables present in _qBounds_ will have their _nPossible_ number read
       from _qbounds

     - _nPossible_ for other numeric variables will be calculated

  """
  numericTypes = [type(1),type(1.0),type(1L)]
  print 'order:',order, len(order)
  print 'qB:',qBounds
  #print 'nQB:',nQBounds, len(nQBounds)
  assert (qBounds and len(order)==len(qBounds)) or (nQBounds and len(order)==len(nQBounds)),\
         'order/qBounds mismatch'
  nVars = len(order)
  nPossible = [-1]*nVars
  cols = range(nVars)
  for i in xrange(nVars):
    if nQBounds and nQBounds[i] != 0:
      nPossible[i] = -1
      cols.remove(i)
    elif len(qBounds[i])>0:
      nPossible[i] = len(qBounds[i])
      cols.remove(i)

  nPts = len(data)
  for i in xrange(nPts):
    for col in cols[:]:
      d = data[i][order[col]]
      if type(d) in numericTypes:
        if int(d) == d:
          nPossible[col] = max(int(d),nPossible[col])
        else:
          nPossible[col] = -1
          cols.remove(col)
      else:
        print 'bye bye col %d: %s'%(col,repr(d))
        nPossible[col] = -1
        cols.remove(col)

  return map(lambda x:int(x)+1,nPossible)



def WritePickledData(outName,data):
  """ writes either a .qdat.pkl or a .dat.pkl file

    **Arguments**

      - outName: the name of the file to be used

      - data: either an _MLData.MLDataSet_ or an _MLData.MLQuantDataSet_

  """
  outFile = open(outName,'wb+')
  varNames = data.GetVarNames()
  qBounds = data.GetQuantBounds()
  ptNames = data.GetPtNames()
  examples = data.GetAllData()

  cPickle.dump(varNames,outFile)
  cPickle.dump(qBounds,outFile)  
  cPickle.dump(ptNames,outFile)  
  cPickle.dump(examples,outFile)
  outFile.close()

def QuantDataToDB(qData,dbName,baseTableName,user='sysdba',password='masterkey'):
  """ fires an _MLData.MLQuantDataSet_ into a database

    **Arguments**

      - qData: an _MLData.MLQuantDataSet_

      - dbName: the name of the database to be opened

      - baseTableName: the table name to contain the data in the database

      - user: the user name to be used to connect to the database

      - password: the password to be used to connect to the database

    **Notes**

      - at the moment this is specific to using *Interbase* with the *gvib*
        adaptor, but that would be straightforward to change.

      - two tables are actually created:

         1) _baseTableName_ contains the quantized data

         2) _baseTableName_QBounds_ contains the quantization bounds

  
  """
  import gvib
  cn = gvib.connect(dbName,user,password)
  c = cn.cursor()
  varNames = qData.varNames
  maxPtNameLen = max(map(len,qData.GetPtNames()))

  valStr = '%s varchar(%d)'%(varNames[0],maxPtNameLen)
  for var in xrange(1,len(varNames)):
    valStr = valStr + ', %s int'%(varNames[var])
  
  try:
    c.execute('drop table %s'%baseTableName)
  except:
    pass
  createStr = 'create table %s (%s)'%(baseTableName,valStr)
  print 'create:',createStr
  c.execute(createStr)
  for pt in qData.GetNamedData():
    vals = map(str,pt)
    vals[0] = "\'%s\'"%vals[0]
    valStr= string.join(vals,',')
    c.execute('insert into %s values (%s)'%(baseTableName,valStr))

  quantName = '%s_QBounds'%(baseTableName)
  maxVarNameLen = max(map(len,varNames))
  strBounds = map(str,qData.GetQuantBounds())
  maxStrBoundLen = max(map(len,strBounds))
  try:
    c.execute('drop table %s'%quantName)
  except:
    pass
  createStr = 'create table %s (variable_name varchar(%d), quant_bounds varchar(%d))'%(quantName,maxVarNameLen,maxStrBoundLen)
  c.execute(createStr)
  for i in xrange(len(varNames)):
    c.execute("insert into %s values ('%s','%s')"%(quantName,varNames[i],strBounds[i]))

  cn.commit()
  
def DBToQuantData(dbName,baseTableName,quantName='',user='sysdba',password='masterkey'):
  """ constructs  an _MLData.MLQuantDataSet_ from a database

    **Arguments**

      - dbName: the name of the database to be opened

      - baseTableName: the table name containing the data in the database

      - quantName: the table name containing the quantization bounds in the database

      - user: the user name to be used to connect to the database

      - password: the password to be used to connect to the database

    **Returns**

       an _MLData.MLQuantDataSet_

    **Notes**

      - at the moment this is specific to using *Interbase* with the *gvib*
        adaptor, but that would be straightforward to change.

      - two tables are actually required:

         1) _baseTableName_ contains the quantized data

         2) _baseTableName_QBounds_ contains the quantization bounds
  
  """
  import gvib
  try:
    cn = gvib.connect(dbName,user,password)
  except:
    print 'cannot connect to database %s'%(dbName)
    return None
  c = cn.cursor()

  if quantName == '':
    quantName = '%s_QBounds'%(baseTableName)
  try:
    c.execute('select * from %s'%quantName)
  except:
    print 'cannot query table %s in database %s'%(quantName,dbName)
    return None
  
  res = c.fetchall()
  varNames = map(lambda x:x[0][:-1],res)
  qBounds = map(lambda x: eval(x[1]),res)

  try:
    c.execute('select * from %s'%baseTableName)
  except:
    print 'cannot query table %s in database %s'%(baseTableName,dbName)
    return None
  res = c.fetchall()
  vals = map(lambda x: map(lambda y: int(y),x[1:]),res)

  ptNames = map(lambda x: x[0],res)
  data = MLData.MLQuantDataSet(vals,qBounds=qBounds,varNames=varNames,
                               ptNames=ptNames)
  return data

def TakeEnsemble(vect,ensembleIds,isDataVect=False):
  """

  >>> v = [10,20,30,40,50]
  >>> TakeEnsemble(v,(1,2,3))
  [20, 30, 40]
  >>> v = ['foo',10,20,30,40,50,1]
  >>> TakeEnsemble(v,(1,2,3),isDataVect=True)
  ['foo', 20, 30, 40, 1]
  


  """
  if isDataVect:
    ensembleIds = [x+1 for x in ensembleIds]
    vect = [vect[0]]+[vect[x] for x in ensembleIds]+[vect[-1]]
  else:
    vect = [vect[x] for x in ensembleIds]
  return vect
    


def DBToData(dbName,tableName,user='sysdba',password='masterkey',dupCol=-1,
             what='*',where='',join='',pickleCol=-1,pickleClass=None,
             ensembleIds=None):
  """ constructs  an _MLData.MLDataSet_ from a database

    **Arguments**

      - dbName: the name of the database to be opened

      - tableName: the table name containing the data in the database

      - user: the user name to be used to connect to the database

      - password: the password to be used to connect to the database

      - dupCol: if nonzero specifies which column should be used to recognize
        duplicates.

    **Returns**

       an _MLData.MLDataSet_

    **Notes**

      - this uses Dbase.DataUtils functionality

  """
  conn = DbConnect(dbName,tableName,user,password)
  res = conn.GetData(fields=what,where=where,join=join,removeDups=dupCol,
                     forceList=1)
  nPts = len(res)
  vals = [None]*nPts
  ptNames = [None]*nPts
  classWorks=True
  for i in range(nPts):
    tmp = list(res[i])
    ptNames[i] = tmp.pop(0)
    if pickleCol>=0:
      if not pickleClass or not classWorks:
        tmp[pickleCol] = cPickle.loads(str(tmp[pickleCol]))
      else:
        try:
          tmp[pickleCol] = pickleClass(str(tmp[pickleCol]))
        except:
          tmp[pickleCol] = cPickle.loads(str(tmp[pickleCol]))
          classWorks=False
      if ensembleIds:
        tmp[pickleCol] = BitUtils.ConstructEnsembleBV(tmp[pickleCol],ensembleIds)
    else:
      if ensembleIds:
        tmp = TakeEnsemble(tmp,ensembleIds,isDataVect=True)
    vals[i] = tmp  
  varNames = conn.GetColumnNames(join=join,what=what)
  data = MLData.MLDataSet(vals,varNames=varNames,ptNames=ptNames)
  return data

def TextToData(reader,ignoreCols=[],onlyCols=None):
  """ constructs  an _MLData.MLDataSet_ from a bunch of text
#DOC
    **Arguments**
      - reader needs to be iterable and return lists of elements
        (like a csv.reader)

    **Returns**

       an _MLData.MLDataSet_

  """

  varNames = reader.next()
  if not onlyCols:
    keepCols = []
    for i,name in enumerate(varNames):
      if name not in ignoreCols:
        keepCols.append(i)
  else:
    keepCols = [-1]*len(onlyCols)
    for i,name in enumerate(varNames):
      if name in onlyCols:
        keepCols[onlyCols.index(name)]=i

  nCols = len(varNames)
  varNames = tuple([varNames[x] for x in keepCols])
  nVars = len(varNames)
  vals = []
  ptNames = []
  for splitLine in reader:
    if len(splitLine):
      if len(splitLine)!=nCols:
        raise ValueError,'unequal line lengths'
      tmp = [splitLine[x] for x in keepCols]
      ptNames.append(tmp[0])
      pt = [None]*(nVars-1)
      for j in range(nVars-1):
        try:
          val = int(tmp[j+1])
        except:
          try:
            val = float(tmp[j+1])
          except:
            val = str(tmp[j+1])
        pt[j] = val    
      vals.append(pt)
  data = MLData.MLDataSet(vals,varNames=varNames,ptNames=ptNames)
  return data

def TextFileToData(fName,onlyCols=None):
  """
  #DOC

  """
  ext = fName.split('.')[-1]
  if ext.upper() == 'CSV':
    #  CSV module distributed with python2.3 and later
    splitter = csv.reader(open(fName,'rU'))
  else:
    splitter = csv.reader(open(fName,'rU'),delimiter='\t')
  return TextToData(splitter,onlyCols=onlyCols)

def InitRandomNumbers(seed):
  """ Seeds the random number generators

    **Arguments**

      - seed: a 2-tuple containing integers to be used as the random number seeds

    **Notes**

      this seeds both the RDRandom generator and the one in the standard
      Python _random_ module

  """
  from pyRDKit import RDRandom
  RDRandom.seed(seed[0])
  import random
  random.seed(seed[0])

def FilterData(inData,val,frac,col=-1,indicesToUse=None,indicesOnly=0):
  """
#DOC
  """
  if frac<0 or frac>1: raise ValueError,'filter fraction out of bounds'
  try:
    inData[0][col]
  except IndexError:
    raise ValueError,'target column index out of range'

  
  # convert the input data to a list and sort them
  if indicesToUse:
    tmp = [inData[x] for x in indicesToUse]
  else:
    tmp = list(inData)
  nOrig = len(tmp)
  sortOrder = range(nOrig)
  sortOrder.sort(lambda x,y,col=col,tmp=tmp:cmp(tmp[x][col],tmp[y][col]))
  tmp = [tmp[x] for x in sortOrder]

  # find the start of the entries with value val
  start = 0
  while start < nOrig and tmp[start][col] != val:
    start += 1
  if  start >= nOrig:
    raise ValueError,'target value (%d) not found in data'%(val)
  
  # find the end of the entries with value val
  finish = start+1
  while finish<nOrig and tmp[finish][col] ==val:
    finish += 1

  # how many entries have the target value?
  nWithVal = finish-start

  # how many don't?
  nOthers = len(tmp)-nWithVal

  currFrac = float(nWithVal) / nOrig
  if currFrac < frac:
    #
    # We're going to keep most of (all) the points with the target value,
    #  We need to figure out how many of the other points we'll 
    #  toss out
    #
    nTgtFinal = nWithVal
    nFinal = int(round(nWithVal / frac))
    nOthersFinal = nFinal - nTgtFinal

    #
    # We may need to reduce the number of targets to keep
    #  because it may make it impossible to hit exactly the
    #  fraction we're trying for.  Take care of that now
    #
    while float(nTgtFinal) / nFinal > frac:
      nTgtFinal -= 1
      nFinal -= 1

  else:
    #
    # There are too many points with the target value,
    #  we'll keep most of (all) the other points and toss a random
    #  selection of the target value points
    #
    nOthersFinal = nOthers
    nFinal = int(round(nOthers/(1-frac)))
    nTgtFinal = nFinal - nOthersFinal

    #
    # We may need to reduce the number of others to keep
    #  because it may make it impossible to hit exactly the
    #  fraction we're trying for.  Take care of that now
    #
    while float(nTgtFinal) / nFinal < frac:
      nOthersFinal -= 1
      nFinal -= 1
    
  others = range(start) + range(finish,nOrig)
  othersTake = permutation(nOthers)
  others = [others[x] for x in othersTake[:nOthersFinal]]

  targets = range(start,finish)
  targetsTake = permutation(nWithVal)
  targets = [targets[x] for x in targetsTake[:nTgtFinal]]
    
  # these are all the indices we'll be keeping
  indicesToKeep = targets+others
  nToKeep = len(indicesToKeep)
  nRej = nOrig-nToKeep

  res = []
  rej = []
  # now pull the points, but in random order
  if not indicesOnly:
    for i in permutation(nOrig):
      if i in indicesToKeep:
        res.append(tmp[i])
      else:
        rej.append(tmp[i])
  else:
    # EFF: this is slower than it needs to be
    for i in permutation(nOrig):
      if not indicesToUse:
        idx = sortOrder[i]
      else:
        idx = indicesToUse[sortOrder[i]]
      if i in indicesToKeep:
        res.append(idx)
      else:
        rej.append(idx)
  return res,rej

def CountResults(inData,col=-1,bounds=None):
  """ #DOC
  """
  counts = {}
  for p in inData:
    if not bounds:
      r = p[col]
    else:
      act = p[col]
      bound = 0
      placed = 0
      while not placed and bound < len(bounds):
        if act < bounds[bound]:
          r = bound
          placed = 1
        else:
          bound += 1
      if not placed:
        r = bound

    counts[r] = counts.get(r,0)+1
  return counts


def RandomizeActivities(dataSet,shuffle=0,runDetails=None):
  """ randomizes the activity values of a dataset

    **Arguments**

      - dataSet: a _ML.Data.MLQuantDataSet_, the activities here will be randomized

      - shuffle: an optional toggle. If this is set, the activity values
        will be shuffled (so the number in each class remains constant)

      - runDetails: an optional CompositeRun object

    **Note**

      - _examples_ are randomized in place

      
  """
  nPossible = dataSet.GetNPossibleVals()[-1]
  nPts = dataSet.GetNPts()
  if shuffle:
    if runDetails: runDetails.shuffled = 1
    acts = dataSet.GetResults()[:]
    random.shuffle(acts)
  else:
    if runDetails: runDetails.randomized = 1
    acts = [random.randint(0,nPossible) for x in len(examples)]
  for i in range(nPts):
    tmp = dataSet[i]
    tmp[-1] = acts[i]
    dataSet[i] = tmp





#------------------------------------
#
#  doctest boilerplate
#
def _test():
  import doctest,sys
  return doctest.testmod(sys.modules["__main__"])

if __name__ == '__main__':
  import sys
  failed,tried = _test()
  sys.exit(failed)
