from pandas import Float64Index, Index
import numpy as np
from pyuvvis.units.abcunits import UnitError, Unit

def _parse_unit(unit, unitdict):
   """ Given a string unit (ie nm), returns the corresponding unit
   class."""
   if unit not in unitdict:
      raise UnitError('Invalid unit "%s".  Choose from %s' % 
                      (unit, sorted(unitdict.keys()) ) )
   return unitdict[unit]  


class ConversionIndex(Index):
   """ Base class for pyuvvis.  To overwrite, requires:
        - replace unitdict with a dictionary from units.py, eg SPECUNITS
        - overwrite convert(), which defines conversions on the unit types.
   Since we are subclassing a numpy array and not a basic python object, 
   we don't write __init__(); rather, __new__ and __array_finalize__ are
   employed (http://docs.scipy.org/doc/numpy/user/basics.subclassing.html)
   
   _forcetype will force any construction to this type.  Even tho it inherits
   from float64index, found that passing an Int64Index to SpecIndex() resulted
   in integer indicies.  
   """

   unitdict = None 
   addnullunit = True
   _forcetype = None 
   

   def __new__(cls, input_array, unit=None):
      """ Unit is valid key of unitdict """
      #Not sure why I have to enfory dtype, but if SpecIndex() of an
      # Int64 index, it remains integer
      if cls._forcetype:
         obj = np.asarray(input_array, dtype=cls._forcetype).view(cls)
      else:
         obj = np.asarray(input_array).view(cls)         
      obj._unit = _parse_unit(unit, cls.unitdict)
      return obj

   # I am not really worred about other constructors yet...
   def __array_finalize__(self, obj):
      """No matter what constructor called, this will get called, so does
      all the housekeeping."""

      if None not in self.unitdict:
         self.unitdict[None] = Unit()
      
      if obj is None: 
         return
      
      # Can be called form slicing or other reasons, and I don't always know
      # if unit is still a string/Non_e, or if it's already a Unit class.
      # Thus, I let both cases work, even though don't know when is what
      unit = getattr(obj, 'unit', None)
      self._id = getattr(obj, '_id', None)
      
      # Necessary for certain instantiations DONT CHANGE
      if isinstance(unit, str) or unit is None:
         self._unit = _parse_unit(unit, self.unitdict)
      else:
         self._unit = unit

   def convert(self, outunit):
      """Convert spectral values based on string outunit.  First converts
      the current unit to the canonical unit (eg, nanometers goes to meters)
      then to the outunit (eg, meters to eV).  This is done through the unit
      methods, .to_canonical() and .from_canonical() where in the case of
      spectral units, canonical refers to meters.
      """
      outunit = _parse_unit(outunit, self.unitdict)
      inunit = self._unit

      # Unit not changed, or set to None
      if outunit.short == inunit.short or not outunit.short:
         return self.__class__(self, unit=outunit.short)

      # If current unit is None, just set new unit
      if not inunit.short:
         return self.__class__(self, unit = outunit.short)

      # Convert non-null unit to another non-null unit   
      else: 
         canonical = inunit.to_canonical(np.array(self))
         arrayout = outunit.from_canonical(canonical)
         return self.__class__(arrayout, unit=outunit.short)      
         

   def _parse_unit(self, unit):
      """ Given a string unit (ie nm), returns the corresponding unit
      class."""
      if unit not in self.unitdict:
         raise UnitError('Invalid unit "%s".  Choose from %s' % 
                         (unit, sorted(self.unitdict.keys()) ) )
      return self.unitdict[unit]      


   #Email list about this distinction
   #def __repr__(self):
      #""" Used internally in code, like if I print self fromin function."""
      #out = super(ConversionIndex, self).__repr__()        
      #return out.replace(self.__class__.__name__, '%s[%s]' %
                         #(self.__class__.__name__, self._unit.short))

   def __unicode__(self):
      """ Returned on printout call.  Not sure why repr not called... """
      out = super(ConversionIndex, self).__unicode__()        
      return out.replace(self.__class__.__name__, '%s[%s]' % 
                         (self.__class__.__name__, self._unit.short))

   # PROMOTED UNIT METHODS
   def __getattr__(self, attr):
      """ Defer attribute call to self._unit"""
      try:
         return getattr(self._unit, attr)
      except AttributeError:
         raise AttributeError('%s has no attribute "%s".' % 
                              (self.__class__.__name__, attr) )

   @property
   def unit(self):
      return self._unit.short

   @property
   def unitshortdict(self):
      """ Return key:shortname; used by TimeSpectra to list output units."""
      return dict((k,v.full) for k,v in self.unitdict.items())
      
   
class ConversionFloat64Index(ConversionIndex, Float64Index):
   """ Float64 conversion index.  Main difference is that Float64Index
   has several properties like "is_all_dates" and "is_unique" that are 
   critical for slicing and other Dataframe operations.  Therefore, we 
   want to retain all these for the Float64Index.  By method res order (MRO),
   they should not overwrite anything define don conversion index.  
   
   More about MRO in python: http://mypythonnotes.wordpress.com/2008/11/01/
                 python-multiple-inheritance-and-the-diamond-problem/ """
   
   _forcetype = 'float64' 
   