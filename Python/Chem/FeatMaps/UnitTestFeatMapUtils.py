# $Id$
#
#  Copyright (C) 2006  greg Landrum 
#
#   @@ All Rights Reserved  @@
#
from pyRDKit import RDConfig
import unittest,sys,os,math
from pyRDKit import Chem
from pyRDKit.Chem.FeatMaps import FeatMaps,FeatMapParser,FeatMapUtils
from pyRDKit.Chem.FeatMaps.FeatMapPoint import FeatMapPoint
from pyRDKit.Geometry import Point3D

def feq(n1,n2,tol=1e-4):
  return abs(n1-n2)<=tol
def pteq(p1,p2,tol=1e-4):
  return feq((p1-p2).LengthSq(),0.0,tol)

class TestCase(unittest.TestCase):
  def setUp(self):
    self.paramTxt="""
BeginParams
  family=Acceptor radius=0.5 profile=Box
EndParams
"""
    self.p = FeatMapParser.FeatMapParser()

  def test1Basics(self):
    txt = self.paramTxt+"""
BeginPoints
  family=Acceptor pos=(1.0, 0.0, 0.0) weight=1.0
  family=Acceptor pos=(1.1, 0.0, 0.0) weight=1.0
  family=Acceptor pos=(3.0, 0.0, 0.0) weight=1.0
EndPoints
    """
    self.p.SetData(txt)
    fm1 = self.p.Parse()

    self.failUnless(fm1.GetNumFeatures()==3)
    self.failIf(FeatMapUtils.MergeFeatPoints(fm1))
    self.failUnless(FeatMapUtils.MergeFeatPoints(fm1,FeatMapUtils.MergeMetric.Distance))
    self.failUnless(fm1.GetNumFeatures()==2)
    self.failUnless(pteq(fm1.GetFeature(0).GetPos(),Point3D(1.05,0,0)))
    self.failUnless(pteq(fm1.GetFeature(1).GetPos(),Point3D(3.0,0,0)))
    
    txt = self.paramTxt+"""
BeginPoints
  family=Acceptor pos=(1.0, 0.0, 0.0) weight=1.0
  family=Acceptor pos=(1.1, 0.0, 0.0) weight=1.0
  family=Acceptor pos=(3.0, 0.0, 0.0) weight=1.0
  family=Acceptor pos=(4.0, 0.0, 0.0) weight=1.0
EndPoints
    """
    self.p.SetData(txt)
    fm1 = self.p.Parse()

    self.failUnless(fm1.GetNumFeatures()==4)
    self.failUnless(FeatMapUtils.MergeFeatPoints(fm1,FeatMapUtils.MergeMetric.Distance))
    self.failUnless(fm1.GetNumFeatures()==2)
    self.failUnless(pteq(fm1.GetFeature(0).GetPos(),Point3D(1.05,0,0)))
    self.failUnless(pteq(fm1.GetFeature(1).GetPos(),Point3D(3.5,0,0)))
    
    txt = self.paramTxt+"""
BeginPoints
  family=Acceptor pos=(1.0, 0.0, 0.0) weight=1.0
  family=Acceptor pos=(1.2, 0.0, 0.0) weight=1.0
  family=Acceptor pos=(1.3, 0.0, 0.0) weight=1.0
  family=Acceptor pos=(4.0, 0.0, 0.0) weight=1.0
EndPoints
    """
    self.p.SetData(txt)
    fm1 = self.p.Parse()

    self.failUnless(fm1.GetNumFeatures()==4)
    self.failUnless(FeatMapUtils.MergeFeatPoints(fm1,FeatMapUtils.MergeMetric.Distance))
    self.failUnless(fm1.GetNumFeatures()==3)
    self.failUnless(pteq(fm1.GetFeature(0).GetPos(),Point3D(1.00,0,0)))
    self.failUnless(pteq(fm1.GetFeature(1).GetPos(),Point3D(1.25,0,0)))
    self.failUnless(pteq(fm1.GetFeature(2).GetPos(),Point3D(4.0,0,0)))

    txt = self.paramTxt+"""
BeginPoints
  family=Acceptor pos=(1.0, 0.0, 0.0) weight=1.0
  family=Acceptor pos=(1.2, 0.0, 0.0) weight=3.0
  family=Acceptor pos=(1.3, 0.0, 0.0) weight=1.0
  family=Acceptor pos=(4.0, 0.0, 0.0) weight=1.0
EndPoints
    """
    self.p.SetData(txt)
    fm1 = self.p.Parse()

    self.failUnless(fm1.GetNumFeatures()==4)
    self.failUnless(FeatMapUtils.MergeFeatPoints(fm1,FeatMapUtils.MergeMetric.Distance,
                                                 mergeMethod=FeatMapUtils.MergeMethod.Average))
    self.failUnless(fm1.GetNumFeatures()==3)
    self.failUnless(pteq(fm1.GetFeature(0).GetPos(),Point3D(1.00,0,0)))
    self.failUnless(pteq(fm1.GetFeature(1).GetPos(),Point3D(1.25,0,0)))
    self.failUnless(pteq(fm1.GetFeature(2).GetPos(),Point3D(4.0,0,0)))

    self.p.SetData(txt)
    fm1 = self.p.Parse()
    self.failUnless(fm1.GetNumFeatures()==4)
    self.failUnless(FeatMapUtils.MergeFeatPoints(fm1,FeatMapUtils.MergeMetric.Distance,
                                                 mergeMethod=FeatMapUtils.MergeMethod.WeightedAverage))
    self.failUnless(fm1.GetNumFeatures()==3)
    self.failUnless(pteq(fm1.GetFeature(0).GetPos(),Point3D(1.00,0,0)))
    self.failUnless(pteq(fm1.GetFeature(1).GetPos(),Point3D(1.225,0,0)))
    self.failUnless(pteq(fm1.GetFeature(2).GetPos(),Point3D(4.0,0,0)))

    self.p.SetData(txt)
    fm1 = self.p.Parse()
    self.failUnless(fm1.GetNumFeatures()==4)
    self.failUnless(FeatMapUtils.MergeFeatPoints(fm1,FeatMapUtils.MergeMetric.Distance,
                                                 mergeMethod=FeatMapUtils.MergeMethod.UseLarger))
    self.failUnless(fm1.GetNumFeatures()==3)
    self.failUnless(pteq(fm1.GetFeature(0).GetPos(),Point3D(1.00,0,0)))
    self.failUnless(pteq(fm1.GetFeature(1).GetPos(),Point3D(1.2,0,0)))
    self.failUnless(pteq(fm1.GetFeature(2).GetPos(),Point3D(4.0,0,0)))

  def _test1BasicsRepeated(self):
    txt = self.paramTxt+"""
BeginPoints
  family=Acceptor pos=(0.7, 0.0, 0.0) weight=1.0
  family=Acceptor pos=(1.0, 0.0, 0.0) weight=1.0
  family=Acceptor pos=(1.2, 0.0, 0.0) weight=1.0
  family=Acceptor pos=(1.3, 0.0, 0.0) weight=1.0
  family=Acceptor pos=(4.0, 0.0, 0.0) weight=1.0
EndPoints
    """
    self.p.SetData(txt)
    fm1 = self.p.Parse()

    self.failUnless(fm1.GetNumFeatures()==5)
    self.failUnless(FeatMapUtils.MergeFeatPoints(fm1,FeatMapUtils.MergeMetric.Distance))
    self.failUnless(fm1.GetNumFeatures()==4)
    self.failUnless(pteq(fm1.GetFeature(0).GetPos(),Point3D(0.7,0,0)))
    self.failUnless(pteq(fm1.GetFeature(1).GetPos(),Point3D(1.0,0,0)))
    self.failUnless(pteq(fm1.GetFeature(2).GetPos(),Point3D(1.25,0,0)))
    self.failUnless(pteq(fm1.GetFeature(3).GetPos(),Point3D(4.0,0,0)))
    
    self.failUnless(FeatMapUtils.MergeFeatPoints(fm1,FeatMapUtils.MergeMetric.Distance))
    self.failUnless(fm1.GetNumFeatures()==3)
    self.failUnless(pteq(fm1.GetFeature(0).GetPos(),Point3D(0.7,0,0)))
    self.failUnless(pteq(fm1.GetFeature(1).GetPos(),Point3D(1.125,0,0)))
    self.failUnless(pteq(fm1.GetFeature(2).GetPos(),Point3D(4.0,0,0)))
    
    self.failUnless(FeatMapUtils.MergeFeatPoints(fm1,FeatMapUtils.MergeMetric.Distance))
    self.failUnless(fm1.GetNumFeatures()==2)
    self.failUnless(pteq(fm1.GetFeature(0).GetPos(),Point3D(0.9125,0,0)))
    self.failUnless(pteq(fm1.GetFeature(1).GetPos(),Point3D(4.0,0,0)))
    
  def test2ScoreBasics(self):
    txt = self.paramTxt+"""
BeginPoints
  family=Acceptor pos=(1.0, 0.0, 0.0) weight=1.0
  family=Acceptor pos=(1.2, 0.0, 0.0) weight=3.0
  family=Acceptor pos=(4.0, 0.0, 0.0) weight=1.0
EndPoints
    """
    self.p.SetData(txt)
    fm1 = self.p.Parse()

    self.failUnless(fm1.GetNumFeatures()==3)
    self.failUnless(FeatMapUtils.MergeFeatPoints(fm1,FeatMapUtils.MergeMetric.Overlap,
                                                 mergeMethod=FeatMapUtils.MergeMethod.Average))
    self.failUnless(fm1.GetNumFeatures()==2)
    self.failUnless(pteq(fm1.GetFeature(0).GetPos(),Point3D(1.1,0,0)))
    self.failUnless(pteq(fm1.GetFeature(1).GetPos(),Point3D(4.0,0,0)))

    txt = self.paramTxt+"""
BeginPoints
  family=Acceptor pos=(1.0, 0.0, 0.0) weight=1.0
  family=Acceptor pos=(1.1, 0.0, 0.0) weight=1.0
  family=Acceptor pos=(1.3, 0.0, 0.0) weight=3.0
  family=Acceptor pos=(4.0, 0.0, 0.0) weight=1.0
EndPoints
    """
    self.p.SetData(txt)
    fm1 = self.p.Parse()

    self.failUnless(fm1.GetNumFeatures()==4)
    self.failUnless(FeatMapUtils.MergeFeatPoints(fm1,FeatMapUtils.MergeMetric.Overlap,
                                                 mergeMethod=FeatMapUtils.MergeMethod.Average))
    self.failUnless(fm1.GetNumFeatures()==3)
    self.failUnless(pteq(fm1.GetFeature(0).GetPos(),Point3D(1.15,0,0)))
    self.failUnless(pteq(fm1.GetFeature(1).GetPos(),Point3D(1.1,0,0)))
    self.failUnless(pteq(fm1.GetFeature(2).GetPos(),Point3D(4.0,0,0)))

    txt = self.paramTxt+"""
BeginPoints
  family=Acceptor pos=(1.0, 0.0, 0.0) weight=1.0
  family=Acceptor pos=(1.2, 0.0, 0.0) weight=1.0
  family=Acceptor pos=(1.6, 0.0, 0.0) weight=3.0
  family=Acceptor pos=(4.0, 0.0, 0.0) weight=1.0
EndPoints
    """
    self.p.SetData(txt)
    fm1 = self.p.Parse()

    self.failUnless(fm1.GetNumFeatures()==4)
    self.failUnless(FeatMapUtils.MergeFeatPoints(fm1,FeatMapUtils.MergeMetric.Overlap,
                                                 mergeMethod=FeatMapUtils.MergeMethod.Average))
    self.failUnless(fm1.GetNumFeatures()==3)
    self.failUnless(pteq(fm1.GetFeature(0).GetPos(),Point3D(1.0,0,0)))
    self.failUnless(pteq(fm1.GetFeature(1).GetPos(),Point3D(1.4,0,0)))
    self.failUnless(pteq(fm1.GetFeature(2).GetPos(),Point3D(4.0,0,0)))

    
    
if __name__ == '__main__':
  unittest.main()

