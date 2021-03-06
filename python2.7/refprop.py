#-------------------------------------------------------------------------------
#Name:              refprop
#Purpose:           Call out fluid properties from REFPROP
#
#Author:            Thelen, B.J.
#                   thelen_ben@yahoo.com
#-------------------------------------------------------------------------------
#
#Recognitions
#-------------------------------------------------------------------------------
#Creators / Developers of REFPROP,
#Lemmon, E.W.,
#Huber, M.L.,
#McLinden, M.O.,
#NIST Standard Reference Database 23:  Reference Fluid Thermodynamic and
#Transport Properties-REFPROP,
#Version 9.1,
#National Institute of Standards and Technology,
#Standard Reference Data Program, Gaithersburg, 2010.
#
#Initial developer of Python link to REFPROP,
#Bruce Wernick
#-------------------------------------------------------------------------------
u''' This Python module compiled and linked the Database REFPROP (REFerence
fluid PROPerties) for usage in Python.

REFPROP software is a proprietary and need to be installed on the computer
in order for this module to function. Please contact the National Institute
ofStandards and Technology (NIST) to obtain REFPROP

The subroutine SETUP must be called to initialize the pure fluid or mixture
components. The call to SETUP will allow the choice of one of three
standard reference states for entropy and enthalpy and will automatically
load the "NIST-recommended" models for the components as well as mixing
rules.The routine SETMOD allows the specification of other models. To
define another reference state, or to apply one of the standard states to a
mixture of a specified composition, the subroutine SETREF may be used.These
additional routines should be called only if the fluids and/or models (or
reference state) are changed. The sequence is:

call SETMOD (optional) or GERG04 (Optional)
call SETUP  (REQUIRED)
call SETKTV (optional)
call PREOS  (optional)
call SETAGA (optional)
call SETREF (optional)

Subroutine PUREFLD allows the user to calculate the properties of a pure
fluid when a mixture has been loaded and the fluid is one of the
constituents in the mixture.

Units
----------------------------------------------------------------------------
temperature                         K
pressure, fugacity                  kPa
density                             mol/L
composition                         mole fraction
quality                             mole basis (moles vapor/total moles)
enthalpy, internal energy           J/mol
Gibbs, Helmholtz free energy        J/mol
entropy, heat capacity              J/(mol.K)
speed of sound                      m/s
Joule-Thompson coefficient          K/kPa
d(p)/d(rho)                         kPa.L/mol
d2(p)/d(rho)2                       kPa.(L/mol)^2
viscosity                           microPa.s (10^-6 Pa.s)
thermal conductivity                W/(m.K)
dipole moment                       debye
surface Tension                     N/m
----------------------------------------------------------------------------
'''
#imports
from __future__ import division
from fnmatch import fnmatch
from os import listdir, path
from platform import system
from copy import copy
from decimal import Decimal
if system() == u'Linux':
    from ctypes import (
        c_long, create_string_buffer, c_double, c_char, byref, RTLD_GLOBAL,
        CDLL)
elif system() == u'Windows':
    from ctypes import (
        c_long, create_string_buffer, c_double, c_char, byref, RTLD_GLOBAL, 
        windll)



#Declarations
#strings
testresult = u''
_setwarning = u'on'
_seterror = u'on'
_seterrordebug = u'off'
_setinputerrorcheck = u'on'
_fpath = u''

#Dict
_fldext = {}
_setupprop = {}
_set = {}

#Intergers
_fixicomp = 0
_nmxpar = 6
_maxcomps = 20

#Nones
(_rp, _gerg04_pre_rec, _setmod_pre_rec, _setup_rec, _setmod_rec, _gerg04_rec,
_setref_rec, _purefld_rec, _setktv_rec, _setaga_rec, _preos_rec) \
    = (None,)*11

#c_long
(_icomp, _jcomp, _kph, _kq, _kguess, _nc, _ixflag, _v, _nroot, _k1, _k2, _k3,
    _ksat, _ierr, _kr) = (c_long(), c_long(), c_long(), c_long(), c_long(),
    c_long(), c_long(), c_long(), c_long(), c_long(), c_long(), c_long(),
    c_long(), c_long(), c_long())

#create_string_buffer
_routine = create_string_buffer(2)
_hrf, _htype, _hmodij, _hmix, _hcode = (
    create_string_buffer(3), create_string_buffer(3), create_string_buffer(3),
    create_string_buffer(3), create_string_buffer(3))
_hname, _hcas = (create_string_buffer(12), create_string_buffer(12))
_hn80 = create_string_buffer(80)
_hpth, _hmxnme, _hfmix, _hbinp, _hmxrul, _hfm, _hcite, _herr, _hfile = (
    create_string_buffer(255), create_string_buffer(255),
    create_string_buffer(255), create_string_buffer(255),
    create_string_buffer(255), create_string_buffer(255),
    create_string_buffer(255), create_string_buffer(255),
    create_string_buffer(255))
_hfld = create_string_buffer(10000)

#C-doubles *
_x, _x0, _xliq, _xvap, _xkg, _xbub, _xdew, _xlkg, _xvkg, _u, _f \
    = ((c_double * _maxcomps)(), (c_double * _maxcomps)(),
    (c_double * _maxcomps)(), (c_double * _maxcomps)(), (c_double * _maxcomps)(),
    (c_double * _maxcomps)(), (c_double * _maxcomps)(), (c_double * _maxcomps)(),
    (c_double * _maxcomps)(), (c_double * _maxcomps)(), (c_double * _maxcomps)())
_fij = (c_double * _nmxpar)()

#c_chars
_hcomp = ((c_char * 3) * _maxcomps)()
#some error with ctypes or refpropdll the following should work but doesnot
#_hfij = ((c_char * 8) * _nmxpar)()
_hfij = ((c_char * (8 * _nmxpar)) * _nmxpar)()

#c_doubles
(_tcrit, _pcrit, _Dcrit, _zcrit, _t, _D, _p, _e, _h, _s, _A, _G, _cv, _cp, _w,
    _Z, _hjt, _xkappa, _beta, _dpdD, _d2pdD2, _dpdt, _dDdt, _dDdp, _spare1,
    _spare2, _spare3, _spare4, _xisenk, _xkt, _betas, _bs, _xkkt, _thrott,
    _pint, _spht, _Ar, _Gr, _dhdt_D, _dhdt_p, _dhdD_t, _dhdD_p, _dhdp_t,
    _dhdp_D, _b, _dbt, _c, _d, _Dliq, _Dvap, _t1, _p1, _D1, _t2, _p2, _D2, _t3,
    _p3, _D3, _csat, _cv2p, _tcx, _qkg, _wmix, _wmm, _ttrp, _tnbpt, _acf, _dip,
    _Rgas, _tmin, _tmax, _Dmax, _pmax, _Dmin, _tbub, _tdew, _pbub, _pdew,
    _Dlbub, _Dvdew, _wliq, _wvap, _de, _sigma, _eta, _h0, _s0, _t0, _p0, _vE,
    _eE, _hE, _sE, _aE, _gE, _pr, _er, _hr, _sr, _cvr, _cpr, _ba, _ca, _dct,
    _dct2, _Fpv, _dadn, _dnadn, _cs, _ts, _Ds, _ps, _ws, _var1, _var2, _q) \
    = (c_double(), c_double(), c_double(), c_double(), c_double(), c_double(),
    c_double(), c_double(), c_double(), c_double(), c_double(), c_double(),
    c_double(), c_double(), c_double(), c_double(), c_double(), c_double(),
    c_double(), c_double(), c_double(), c_double(), c_double(), c_double(),
    c_double(), c_double(), c_double(), c_double(), c_double(), c_double(),
    c_double(), c_double(), c_double(), c_double(), c_double(), c_double(),
    c_double(), c_double(), c_double(), c_double(), c_double(), c_double(),
    c_double(), c_double(), c_double(), c_double(), c_double(), c_double(),
    c_double(), c_double(), c_double(), c_double(), c_double(), c_double(),
    c_double(), c_double(), c_double(), c_double(), c_double(), c_double(),
    c_double(), c_double(), c_double(), c_double(), c_double(), c_double(),
    c_double(), c_double(), c_double(), c_double(), c_double(), c_double(),
    c_double(), c_double(), c_double(), c_double(), c_double(), c_double(),
    c_double(), c_double(), c_double(), c_double(), c_double(), c_double(),
    c_double(), c_double(), c_double(), c_double(), c_double(), c_double(),
    c_double(), c_double(), c_double(), c_double(), c_double(), c_double(),
    c_double(), c_double(), c_double(), c_double(), c_double(), c_double(),
    c_double(), c_double(), c_double(), c_double(), c_double(), c_double(),
    c_double(), c_double(), c_double(), c_double(), c_double(), c_double(),
    c_double(), c_double(), c_double())
         


#classes
class _Setuprecord():
    u'record setmod, setup, setktv, setref, purefld input values for def reset'
    object_list = []

    #add record
    def __init__(self, record, objectname):
        self.record = record
        self.objectname = objectname
        self.object_list.append(self.objectname)

    #del record
    def __del__(self):
        self.object_list.remove(self.objectname)


class SetWarning(object):
    u'Return RefpropdllWarning status (on / off)'
    def __repr__(self):
        return _setwarning
    @staticmethod
    def on():
        u'Sets RefpropdllWarning on, initiate Error on Refpropdll ierr value < 0'
        global _setwarning
        _setwarning = u'on'
        if u'SetWarng' in _set: _set.pop(u'SetWarning')
        return _prop()
    @staticmethod
    def off():
        u'Sets RefpropdllWarning off, no Error raised on Refpropdll ierr value < 0'
        global _setwarning
        _setwarning = u'off'
        _set[u'SetWarning'] = u'off'
        return _prop()


class SetError(object):
    u'Return RefpropdllError status (on / off)'
    def __repr__(self):
        return _seterror
    @staticmethod
    def on():
        u'Sets RefpropdllError on, initiate Error on Refpropdll ierr value != 0'
        global _seterror
        _seterror = u'on'
        if u'SetError' in _set: _set.pop(u'SetError')
        return _prop()
    @staticmethod
    def off():
        u'Sets RefpropdllError off, no Error raised on Refpropdll ierr value != 0'
        global _seterror
        _seterror = u'off'
        _set[u'SetError'] = u'off'
        return _prop()


class SetErrorDebug(object):
    u'Return SetErrorDebug status (on / off)'
    def __repr__(self):
        return _seterrordebug
    @staticmethod
    def on():
        u'Sets error debug mode on, displays error message only'
        global _seterrordebug
        _seterrordebug = u'on'
        _set[u'SetDebug'] = u'on'
        return _prop()
    @staticmethod
    def off():
        u'Sets error debug mode off, displays error message only'
        global _seterrordebug
        _seterrordebug = u'off'
        if u'SetDebug' in _set: _set.pop(u'SetDebug')
        return _prop()


class SetInputErrorCheck(object):
    u'Return SetInputErrorCheck status (on / off)'
    def __repr__(self):
        return _setinputerrorcheck
    @staticmethod
    def on():
        u'Sets errorinputerror mode on, displays input error message'
        global _setinputerrorcheck
        _setinputerrorcheck = u'on'
        if u'SetInputErrorCheck' in _set: _set.pop(u'SetInputErrorCheck')
        return _prop()
    @staticmethod
    def off():
        u'Sets errorinputerror mode off, no input error displays message'
        global _setinputerrorcheck
        _setinputerrorcheck = u'off'
        _set[u'SetInputErrorCheck'] = u'off'
        return _prop()


class RefpropError(Exception):
    u'General RepropError for python module'
    pass


class RefpropinputError(RefpropError):
    u'Error for incorrect input'
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)


class RefproproutineError(RefpropError):
    u'Error if routine input is unsupported'
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)


class RefpropdllError(RefpropError):
    u'General RepropError from refprop'
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)


class RefpropicompError(RefpropError):
    u'Error for incorrect component no input'
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)


class RefpropnormalizeError(RefpropError):
    u'Error if sum component input does not match value 1'
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)


class RefpropWarning(RefpropError):
    u'General Warning for python module'
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)


class RefpropdllWarning(RefpropWarning):
    u'General RepropWarning from refprop'
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)


class SetupWarning(RefpropWarning):
    u'General SetupWarning from refprop'
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)


class FluidModel():
    u'''return string of current loaded fluid model

    array includes:
    setmod / gerg04
    setup
    setktv
    preos
    setaga
    setref
    purefld'''
    def __repr__(self):
        global _setup_rec, _setmod_rec, _gerg04_rec, _setref_rec, _purefld_rec
        global _setktv_rec, _setaga_rec, _preos_rec
        fldsetup = u''
        if u'_setmod_rec' in _Setuprecord.object_list:
            fldsetup += u'setmod ==> ' + unicode(_setmod_rec.record) + u'\n'
        if u'_gerg04_rec' in _Setuprecord.object_list:
            fldsetup += u'gerg04 ==> ' + unicode(_gerg04_rec.record) + u'\n'
        if u'_setup_rec' in _Setuprecord.object_list:
            fldsetup += u'setup ==> ' + unicode(_setup_rec.record) + u'\n'
        if u'_setktv_rec' in _Setuprecord.object_list:
            fldsetup += u'setktv ==> ' + unicode(_setktv_rec.record) + u'\n'
        if u'_preos_rec' in _Setuprecord.object_list:
            fldsetup += u'preos ==> ' + unicode(_preos_rec.record) + u'\n'
        if u'_setaga_rec' in _Setuprecord.object_list:
            fldsetup += u'setaga ==> ' + unicode(_setaga_rec.record) + u'\n'
        if u'_setref_rec' in _Setuprecord.object_list:
            fldsetup += u'setref ==> ' + unicode(_setref_rec.record) + u'\n'
        if u'_purefld_rec' in _Setuprecord.object_list:
            fldsetup += u'purefld ==> ' + unicode(_purefld_rec.record) + u'\n'
        return fldsetup



#Functions
#additional functions (not from refprop)
def _checksetupmodel(model):
    u'Raise warning if multiple models are being set'
    models = []
    #add setmod if called already
    if u'_setmod_rec' in _Setuprecord.object_list:
        models.append(u'setmod')
    #add setktv if called already
    if u'_setktv_rec' in _Setuprecord.object_list:
        models.append(u'setktv')
    #add gerg04 if called already
    if u'_gerg04_rec' in _Setuprecord.object_list:
        models.append(u'gerg04')
    #add called model if not included already
    if model not in models:
        models.append(model)
    #raise warning on multiple model calls and if warning is on
    if len(models) > 1 and unicode(SetWarning()) == u'on':
        raise SetupWarning(u'''Warning, calling multiple model setups (setmod,
        setktv and gerg04 and others) could result in unexpected results.
        Furthermore these multiple model calls are not supported by function
        "resetup' and consequentely in the extention module "multiRP"''')


def _outputierrcheck(ierr, herr, defname, prop):
    #_ierr correction, some unknown reason the value is
    # increased by 2**32
    ierr_max = 9999
    ierr_corr = 2**32
    if ierr > ierr_max:
        ierr = ierr - ((ierr + ierr_max) // ierr_corr) * ierr_corr
    def mes_string(ERorWA):
        string = u'*' * 80 + u'\n'
        string += u'*' * 80 + u'\n'
        string += ERorWA + u' raised' + u'\n'
        string += u'setup details' + u'\n'
        string += unicode(FluidModel()) + u'\n'
        string += u'refprop dll call details' + u'\n'
        string += unicode(defname) + u'\n'
        string += u'error details' + u'\n'
        string += unicode(ierr) + u'\n'
        string += unicode(herr) + u'\n'
        string += u'prop output' + u'\n'
        string += unicode(prop) + u'\n'
        string += u'*' * 80 + u'\n'*3
        return string
    if ierr < 0 \
    and unicode(SetWarning()) == u'on' \
    and unicode(SetError()) == u'on': #raise warning
        #warning string
        if unicode(SetErrorDebug()) == u'on':
            print mes_string(u'warning')
        raise RefpropdllWarning(herr.decode(u'utf-8'))
    elif ierr > 0 and unicode(SetError()) == u'on': #raise error
        #error string
        if unicode(SetErrorDebug()) == u'on':
            print mes_string(u'error')
        raise RefpropdllError(herr.decode(u'utf-8'))


def _prop(**prop):
    global _fixicomp, _setupprop, _set
    prop.update(_setupprop)
    prop.update(_set)

    #local declarations
    icomp = prop.get(u'icomp')
    jcomp = prop.get(u'jcomp')
    nc = prop.get(u'nc')
    hfld = prop.get(u'hfld')
    _fixicomp = prop.get(u'fixicomp')
    ierr = prop.get(u'ierr')
    
    #one time hfld correction by icomp
    if icomp != None and nc != None:
        if icomp == 0 or icomp > nc:
            raise RefpropicompError (u'undefined "icomp: ' +
            unicode(icomp) + u'" value, select mixture component ' +
            u'number between 1 and ' + unicode(nc))
        prop[u'icomp'] = [icomp, hfld[icomp - 1]]

    #one time hfld correction by jcomp
    if jcomp != None and nc != None:
        if jcomp == 0 or jcomp > nc:
            raise RefpropicompError (u'undefined "jcomp: ' +
            unicode(jcomp) + u'" value, select mixture component ' +
            u'number between 1 and ' + unicode(nc))
        prop[u'jcomp'] = [jcomp, hfld[jcomp - 1]]

    #multiple time hfld correction by fixicomp / purefld
    if _fixicomp != None:
        del prop[u'fixicomp']

    #assign purefluid in prop
    if nc != None and _fixicomp != None and _fixicomp > nc:
        raise RefpropicompError (u'undefined "icomp: ' +
                                  unicode(_fixicomp) +
                                  u'" value, select mixture component ' +
                                  u'number below ' + unicode(nc))
    elif _fixicomp == 0:
        if u'purefld' in prop: del prop[u'purefld']
    elif nc != None and _fixicomp != None and 0 < _fixicomp <= nc:
        prop[u'purefld'] = [_fixicomp, hfld[_fixicomp - 1]]

    #raise error
    if ierr != None:
        _outputierrcheck(ierr, prop[u'herr'], prop[u'defname'], prop)
        del prop[u'ierr'], prop[u'herr'], prop[u'defname']

    return prop


def _inputerrorcheck(deflocals):
    if unicode(SetInputErrorCheck()) == u'off':
        return None
    #from time import time#
    checkstring = [u'hmxnme', u'hrf', u'htype', u'hmix', u'path', u'routine',
                   u'hmodij', u'hfmix']
    checkint = [u'icomp', u'kph', u'nc', u'ixflag', u'kguess', u'ksat', u'jcomp', u'kq']
    checkfloat = [u't', u'D', u'h0', u's0', u't0', u'p0', u's', u'h', u'e', u'p', u'var1',
                  u'var2', u'tbub', u'tdew', u'pbub', u'pdew', u'Dlbub', u'Dvdew',
                  u'q', u'qkg', u'v']
    checklistcomp = [u'x', u'xkg', u'xbub', u'xdew', u'xlkg', u'xvkg']
    checklist = [u'fij', u'x0']
    checkliststring = [u'hfld', u'hcomp']

    for key in deflocals:
        value = deflocals[key]
        if key in checkstring:
            if not type(value) == unicode:
                raise RefpropinputError (u'expect "str" input for ' + key +
                                          u' instead of "' +
                                          unicode(value.__class__) +u'"')
        elif key in checkint:
            if not type(value) == int:
                raise RefpropinputError (u'expect "int" input for ' +
                                          key + u' instead of "' +
                                          unicode(value.__class__) +u'"')
        elif key in checkfloat:
            if not type(value) == float \
            and not type(value) == int:
                raise RefpropinputError (u'expect "float" or "int" input for ' +
                                          key + u' instead of "' +
                                          unicode(value.__class__) +u'"')
        elif key in checklistcomp:
            if not value: pass
            else:
                lenvalue = len(value)
                if not type(value) == list:
                    raise RefpropinputError(u'expect "list" input for ' +
                                             key + u' instead of "' +
                                             unicode(value.__class__) +
                                             u'"')
                elif lenvalue != _nc_rec.record:
                    if u'_purefld_rec' in _Setuprecord.object_list \
                    and lenvalue != 1:
                        raise RefpropicompError(u'input value ' + key +
                                                 u' does not match the setup '
                                                 u'fluid selection.')
                    elif u'_purefld_rec' not in _Setuprecord.object_list:
                        raise RefpropicompError(u'input value ' + key
                                                 + u' does not match the setup '
                                                 + u'fluid selection')
                if sum(value) != 1:
                    raise RefpropnormalizeError(u'sum input value '
                                                 + key + u'is unequal to 1')
        elif key in checklist:
            if not type(value) == list:
                raise RefpropinputError (u'expect "list" input for ' +
                                          key + u' instead of "' +
                                          unicode(value.__class__) +u'"')
            elif len(value) > _nmxpar:
                raise RefpropinputError (u'input value ' + key
                                          + u' larger then max. value '
                                          + unicode(_nmxpar))
        elif key in checkliststring:
            for each in value:
                if type(each) == list:
                    for other in each:
                        if not type(other) == unicode:
                            raise RefpropinputError (u'expect "list of str"' +
                                u''' or "strs's" input for ''' + unicode(each) +
                                u' instead of "' + unicode(other.__class__) +u'"')
                elif not type(each) == unicode:
                    raise RefpropinputError (u'expect "list of str" or' +
                        u''' "strs's" input for ''' + unicode(each)
                        + u' instead of "' + unicode(each.__class__) +u'"')


def normalize(x):
    u'''Normalize the sum of list x value's to 1'''
    lsum = sum
    x = [Decimal(each) for each in x]
    norm = lsum(x)
    while float(norm) != 1:
        x = [each / norm for each in x]
        norm = lsum(x)
    x = [float(each) for each in x]
    return _prop(x = x)


def getphase(fld):
    u'''Return fluid phase

    input:
        fld--fluid dictionary containing:
            p--pressure
            t--temperature
            x--fluid composition
            q--quality (optional)*
            h--enthalpy (optional)*
            s--entropy (optional)*
                *one of these three needs to be included
    output:
        fluid phase:
            "vapor"--vapor phase
            "saturated vapor"--fluid at dew point
            "gas"--gasious phase (e.g. above critical temperature
            "liquid"--liquid phase
            "saturated liquid"--fluid at bubble point
            "compressible liquid"--(e.g. above critical pressure)
            "Supercritical fluid"
            "2 phase"--both liquid and vapor phase"'''
    _inputerrorcheck(locals())
    #get critical parameters
    crit = critp(fld[u'x'])
    #check if fld above critical pressure
    if fld[u'p'] > crit[u'pcrit']:
        #check if fld above critical pressure
        if fld[u't'] > crit[u'tcrit']:
            return u"Supercritical fluid"
        else:
            return u"compressible liquid"
    #check if fld above critical pressure
    elif fld[u't'] > crit[u'tcrit']:
        return u"gas"
    #check if ['q'] in fld
    if not u'q' in fld:
        if u'h' in fld:
            fld[u'q'] = flsh(u'ph', fld[u'p'], fld[u'h'], fld[u'x'])[u'q']
        elif u's' in fld:
            fld[u'q'] = flsh(u'ps', fld[u'p'], fld[u's'], fld[u'x'])[u'q']
    #check q
    if fld[u'q'] > 1:
        return u"vapor"
    elif fld[u'q'] == 1:
        return u"saturated vapor"
    elif 0 < fld[u'q'] < 1:
        return u"2 phase"
    elif fld[u'q'] == 0:
        return u"saturated liquid"
    elif fld[u'q'] < 0:
        return u"liquid"


def fluidlib():
    u'''Displays all fluids and mixtures available on root directory. If root
    other then default directories:
            'c:/program files/refprop/'
            'c:/program files (x86)/refprop/'
            '/usr/local/lib/refprop/
    call setpath to correct'''
    return _fluidextention()


def _fluidextention():
    u"""return fluid library"""
    global _fldext, _fpath
    if _fldext == {}:
        fldext = {}
        fluidslistdir = listdir(_fpath + u'fluids/')
        mixtureslistdir = listdir(_fpath + u'mixtures/')
        fldext[_fpath + u'fluids/'] = [(each[:-4].upper()) for each in
                                            fluidslistdir if
                                            fnmatch(each, u'*.FLD')]
        fldext[_fpath + u'fluids/'].extend([each for each in fluidslistdir
                                                 if fnmatch(each, u'*.PPF')])
        fldext[_fpath + u'mixtures/'] = [(each[:-4].upper()) for each in
                                              mixtureslistdir if fnmatch
                                              (each, u'*.MIX')]
        _fldext = fldext.copy()
    return _fldext


def resetup(prop, force=False):
    u'''Resetup models and re-initialize  arrays.

    This will compare the loaded models vs requested model and re-setup
    refprop models if deemed required in the following sequence:
        setmod / gerg04
        setup
        setktv
        preos
        setaga
        setref
        purefld

    This enables calculating of dual fluid flows through exchangers, static
    mixures etc.

    input:
        props--standard dictinary output from refprop functions
        force--force resetup (True or False (standard input)'''
    global _gerg04_pre_rec, _setmod_pre_rec
    prop = setup_details(prop)
    #only resetup if loaded models are unequal to request (or force)
    if force == True or setup_setting() != prop:
        #delete any pre-setup request such as gerg04 and setmod
        if u'_setmod_pre_rec' in _Setuprecord.object_list:
            _setmod_pre_rec = None
        if u'_gerg04_pre_rec' in _Setuprecord.object_list:
            _gerg04_pre_rec = None

        #initialize setmod if deemed req.
        stmd = prop.get(u'setmod')
        if stmd != None:
            setmod(stmd[u'htype'],
                   stmd[u'hmix'],
                   stmd[u'hcomp'])

        #initialize gerg04 if deemed req.
        grg4 = prop.get(u'gerg04')
        if grg4 != None:
            gerg04(grg4[u'ixflag'])

        #initialize setup:
        hmxnme = prop.get(u'hmxnme')
        if hmxnme != None:
            setup(prop[u'hrf'],  hmxnme, hfmix=prop[u'hfmix'])
        else:
            setup(prop[u'hrf'],  prop[u'hfld'], hfmix=prop[u'hfmix'])

        #initialize setktv
        stktv = prop.get(u'setktv')
        if stktv != None:
            setktv(stktv[u'icomp'],
                   stktv[u'jcomp'],
                   stktv[u'hmodij'],
                   stktv[u'fij'],
                   stktv[u'hfmix'])

        #initialize preos
        prs = prop.get(u'preos')
        if prs != None:
            preos(prs[u'ixflag'])

        #initialize setaga
        stg = prop.get(u'setaga')
        if stg != None:
            setaga()

        #initialize setref
        strf = prop.get(u'setref')
        if strf != None:
            if not u'ixflag' in strf:
                prop[u'setref'][u'ixflag'] = 1
            if not u'x0' in strf:
                prop[u'setref'][u'x0'] = [1]
            if not u'h0' in strf:
                prop[u'setref'][u'h0'] = 0
            if not u's0' in strf:
                prop[u'setref'][u's0'] = 0
            if not u't0' in strf:
                prop[u'setref'][u't0'] = 273
            if not u'p0' in strf:
                prop[u'setref'][u'p0'] =100
            setref(strf[u'hrf'][0],
                   strf[u'ixflag'],
                   strf[u'x0'],
                   strf[u'h0'],
                   strf[u's0'],
                   strf[u't0'],
                   strf[u'p0'])
            if len(strf[u'hrf']) == 2:
                setref(strf[u'hrf'][1],
                       strf[u'ixflag'],
                       strf[u'x0'],
                       strf[u'h0'],
                       strf[u's0'],
                       strf[u't0'],
                       strf[u'p0'])

        #initialize purefld
        prfld = prop.get(u'purefluid')
        if prfld != None:
            purefld(prfld[0])

        #reset SetError
        if u'SetError' in prop:
            SetError.off()
        else: SetError.on()

        #reset SetWarning
        if u'SetWarning' in prop:
            SetWarning.off()
        else: SetWarning.on()

        #reset SetErrorDebug
        if u'SetDebug' in prop:
            SetErrorDebug.on()
        else: SetErrorDebug.off()

        #reset SetInputErrorCheck
        if u'SetInputErrorCheck' in prop:
            SetInputErrorCheck.off()
        else: SetInputErrorCheck.on()

    return setup_details(_prop())


def setup_setting():
    u'''Returns current loaded setup settings
    output--Minimized dict. with basic refprop settings'''
    return setup_details(_prop())


def setup_details(prop):
    u'''Returns basic setup details of input fluid.

    Setup details from the following module functions:
        setmod / gerg04
        setup
        setktv
        preos
        setags
        setref
        purefld

    input:
        prop--standard dictinary output from refprop functions
    output
        prop--Minimized dict. with basic refprop settings'''
    prps = {}

    if prop.__class__ == dict:
        #setmod
        if u'setmod' in prop:
            prps[u'setmod'] = prop[u'setmod']

        #gerg04
        if u'gerg04' in prop:
            prps[u'gerg04'] = prop[u'gerg04']

        #setup
        if u'hrf' in prop:
            prps[u'hrf'] = prop[u'hrf']
        if u'hfld' in prop:
            prps[u'hfld'] = prop[u'hfld']
        if u'hfmix' in prop:
            prps[u'hfmix'] = prop[u'hfmix']
        if u'hmxnme' in prop:
            prps[u'hmxnme'] = prop[u'hmxnme']
        if u'nc' in prop:
            prps[u'nc'] = prop[u'nc']

        #setktv
        if u'setktv' in prop:
            prps[u'setktv'] = prop[u'setktv']

        #preos
        if u'preos' in prop:
            prps[u'preos'] = prop[u'preos']

        #setaga
        if u'setaga' in prop:
            prps[u'setaga'] = prop[u'setaga']

        #setref
        if u'setref' in prop:
            prps[u'setref'] = prop[u'setref']

        #purefld
        if u'purefld' in prop:
            prps[u'purefld'] = prop[u'purefld']

        #seterror
        if u'SetError' in prop:
            prps[u'SetError'] = u'off'

        #setwarning
        if u'SetWarning' in prop:
            prps[u'SetWarning'] = u'off'

        #seterrordebug
        if u'SetDebug' in prop:
            prps[u'SetDebug'] = u'on'

        #setinputerrorceck
        if u'SetInputErrorCheck' in prop:
            prps[u'SetInputErrorCheck'] = u'off'

    return prps


def _test():
    u'''execute detailed test run of refprop'''
    import rptest
    rptest.settest(u'refprop')


def test(criteria=0.00001):
    u'''verify that the user's computer is returning proper calculations The
    calculated values are compared with NIST calculated values.

    The percent difference between Calculated and NIST should be within the
    acceptance criteria '0.00001' is standard.

    input:
        criteria--acceptance criteria between Calculated and NIST value
    output:
        print screen of NIST value, Calculated value, abs. difference and
        True / False for acceptance.'''
    global testresult
    truefalse = True
    testresult = u''

    #create def for printout
    def printresults(nist, calculated, truefalse):
        global testresult
        calculated = float(calculated)
        testresult += u'\nNIST = ' + unicode(nist)
        testresult += u'\nCalculated = ' + unicode(calculated)
        testresult += u'\nabs relative difference = ' + unicode(
            abs((nist - calculated) / nist))
        testresult += u'\n' + unicode(abs((nist - calculated) / nist) <
            criteria) + u'\n\n'
        truefalse = truefalse and abs((nist - calculated) / nist) < criteria
        return truefalse

    #SetWarning off due to many warnings displayed
    if unicode(SetWarning()) == u'off':
        sw = SetWarning.off
    elif unicode(SetWarning()) == u'on':
        sw = SetWarning.on
        SetWarning.off()

    #test no. 1
    prop = setup(u'def', u'air')
    prop = wmol(prop[u'x'])
    testresult += u'check molar mass of air'
    truefalse = printresults(28.958600656, prop[u'wmix'], truefalse)

    #test no. 2
    setup(u'def', u'argon')
    prop = flsh(u'pD', 2 * 1000, 15 / wmol([1])[u'wmix'], [1])
    testresult += u'check temperature of Argon'
    truefalse = printresults(637.377588657857, prop[u't'], truefalse)

    #test no. 3
    setup(u'def', u'r134a')
    prop = flsh(u'tD', 400, 50 / wmol([1])[u'wmix'], [1])
    testresult += u'check pressure of r134a'
    truefalse = printresults(1.45691892789737, prop[u'p'] / 1000, truefalse)

    ##test no. 4
    #setup('def', 'ethylene')
    #setref(ixflag=2, x0=[1])
    #wmix = wmol([1])['wmix']
    #prop = flsh('ts', 300, 3 * wmix, [1])
    #testresult += 'check enthalphy of ethylene'
    #truefalse = printresults(684.996521090598, prop['h'] / wmix, truefalse)
    ##NIST(as per spreadsheet) = 684.996521090598
    ##Calculated(confirmed by NIST GUI) = 651.5166149584808

    #test no. 5
    setup(u'def', u'oxygen')
    prop = trnprp(100, tprho(100, 1 * 1000, [1], 1)[u'D'], [1])
    testresult += u'check Viscosity of Oxygen'
    truefalse = printresults(153.886680663753, prop[u'eta'], truefalse)

    #test no. 6
    setup(u'def', u'nitrogen')
    prop = trnprp(100, satt(100, [1], 1)[u'Dliq'], [1])
    testresult += u'check Thermal Conductivity of Nitrogen'
    truefalse = printresults(100.111748964945, prop[u'tcx'] * 1000, truefalse)

    #test no. 7
    setup(u'def', u'air')
    x = setup(u'def', u'air')[u'x']
    setref(ixflag=2, x0=x)
    wmix = wmol(x)[u'wmix']
    prop = tprho(((70 - 32) * 5 / 9) + 273.15, 14.7 / 14.50377377 * (10**5) / 1000, x)
    testresult += u'check Density of Air'
    truefalse = printresults(0.0749156384666842, prop[u'D'] * wmix * 0.062427974,
                             truefalse)

    #test no. 8
    setup(u'def', u'R32', u'R125')
    x = [0.3, 0.7]
    u'''Use the following line to calculate enthalpies and entropies on a
    reference state based on the currently defined mixture, or to change to
    some other reference state. The routine does not have to be called, but
    doing so will cause calculations to be the same as those produced from
    the graphical interface for mixtures.'''
    setref(ixflag=2, x0=x)
    prop = flsh(u'ps', 10 * 1000, 110, x)
    testresult += u'check enthalpy of R32 / R125'
    truefalse = printresults(23643.993624382, prop[u'h'], truefalse)

    #test no. 9
    setup(u'def', u'ethane', u'butane')
    x = xmole([0.5, 0.5])[u'x']
    setref(ixflag=2, x0=x)
    wmix = wmol(x)[u'wmix']
    prop = flsh(u'dh', 30 * 0.45359237 / 0.028316846592 / wmix, 283 *
                    1.05435026448889 / 0.45359237 * wmix, x)
    testresult += u'check Temperature of Ethene / Butane'
    truefalse = printresults(298.431320311048, ((prop[u't'] - 273.15) * 9 / 5) + 32,
                             truefalse)

    #test no. 10
    setup(u'def', u'ammonia', u'water')
    x = [0.4, 0.6]
    setref(ixflag=2, x0=x)
    prop = flsh(u'tp', ((300 - 32) * 5 / 9) + 273.15, 10000 / 14.50377377 *
                    (10**5) / 1000, x)
    testresult += u'check speed of Sound of Ammonia / water'
    truefalse = printresults(5536.79144924071, prop[u'w'] * 1000 / 25.4 / 12,
                             truefalse)

    #test no. 11
    setup(u'def', u'r218', u'r123')
    x = [0.1, 0.9]
    setref(ixflag=2, x0=x)
    wmix = wmol(x)[u'wmix']
    prop = flsh(u'ph', 7 * 1000, 180 * wmix, x)
    testresult += u'check Density of R218 / R123'
    truefalse = printresults(1.60040403489036, prop[u'D'] * wmix / 1000, truefalse)

    #test no. 12
    setup(u'def', u'methane', u'ethane')
    x = xmole(normalize([40, 60])[u'x'])[u'x']
    wmix = wmol(x)[u'wmix']
    prop = flsh(u'tD', 200, 300 / wmix, x)
    prop = qmass(prop[u'q'], prop[u'xliq'], prop[u'xvap'])
    testresult += u'check quality of methane / ethane'
    truefalse = printresults(0.0386417701326453, prop[u'qkg'], truefalse)

    #test no. 13
    setup(u'def', u'methane', u'ethane')
    x = xmole(normalize([40, 60])[u'x'])[u'x']
    setref(ixflag=2, x0=x)
    prop = flsh(u'tp', 200, 2.8145509 * 1000, x)
    prop = qmass(prop[u'q'], prop[u'xliq'], prop[u'xvap'])
    testresult += u'check quality of methane / ethane'
    truefalse = printresults(0.0386406167132601, prop[u'qkg'], truefalse)
    #NIST = 0.0386406167132601
    #Calculated = 1.0297826927241274

    #test no. 14
    setup(u'def', u'methane', u'ethane')
    x = xmole(normalize([40, 60])[u'x'])[u'x']
    setref(ixflag=2, x0=x)
    prop = flsh(u'tp', 200, 2814.5509, x)
    testresult += u'check quality of methane / ethane'
    truefalse = printresults(0.0500926636198064, prop[u'q'], truefalse)

    #test no. 15
    setup(u'def', u'octane')
    wmix = wmol([1])[u'wmix']
    prop = satt(100 + 273.15, [1])
    Dliq = prop[u'Dliq']
    Dvap = prop[u'Dvap']
    prop = therm(100 + 273.15, Dliq, [1])
    hliq = prop[u'h']
    prop = therm(100 + 273.15, Dvap, [1])
    hvap = prop[u'h']
    testresult += u'check Heat of Vaporization of Octane'
    truefalse = printresults(319.167499870568, (hvap - hliq) / wmix, truefalse)

    #test no. 16
    setup(u'def', u'butane', u'hexane')
    x = [0.25, 0.75]
    setref(ixflag=2, x0=x)
    testresult += u'check viscosity of Butane / Hexane'
    truefalse = printresults(283.724837443674,
                             trnprp(300, flsh(u'th', 300, -21 * wmol(x)[u'wmix'],
                                              x, 2)[u'D'], x)[u'eta'],
                             truefalse)

    #test no. 17
    setup(u'def', u'CO2', u'nitrogen')
    x = xmole([0.5, 0.5])[u'x']
    setref(ixflag=2, x0=x)
    wmix = wmol(x)[u'wmix']
    prop = flsh(u'th', 250, 220 * wmix, x, 2)
    prop = trnprp(250, prop[u'D'], x)
    testresult += u'check Thermal Conductivity of CO2 / Nitrogen'
    truefalse = printresults(120.984794685581, prop[u'tcx'] * 1000, truefalse)

    #test no. 18
    setup(u'def', u'ethane', u'propane')
    prop = satt(300, [0.5, 0.5])
    prop = dielec(300, prop[u'Dvap'], [0.5, 0.5])
    testresult += u'check Dielectric Constant of Ethane / Propane'
    truefalse = printresults(1.03705806204418, prop[u'de'], truefalse)

    #test no. 19
    prop = setup(u'def', u'R410A')
    testresult += u'check Mole Fraction of R410A'
    truefalse = printresults(0.697614699375863, prop[u'x'][0], truefalse)

    #test no. 20
    prop = xmass(prop[u'x'])
    testresult += u'check mass Fraction of R410A'
    truefalse = printresults(0.5, prop[u'xkg'][0], truefalse)

    #test no. 21
    prop = xmole(prop[u'xkg'])
    testresult += u'check mole Fraction of R410A'
    truefalse = printresults(0.697614699375862, prop[u'x'][0], truefalse)

    #test no. 22
    setup(u'def', u'Methane', u'Ethane', u'Propane', u'Butane')
    x = [0.7, 0.2, 0.05, 0.05]
    setref(ixflag=2, x0=x)
    wmix = wmol(x)[u'wmix']
    prop = flsh(u'td', 150, 200 / wmix, x)
    Dliq = prop[u'Dliq']
    wmix = wmol(prop[u'xliq'])[u'wmix']
    testresult += u'check Liquid Density of Methane / Ethane / Propane / Butane'
    truefalse = printresults(481.276038325628, Dliq * wmix, truefalse)

    #restore SetWarning to original value
    sw()

    return(truefalse)


def psliq(p, s, x):
    u'''flsh1 calculations with boundery check, raise RefpropinputError when
    input is outside bounderies

    Inputs:
        p--pressure [kPa]
        s--entropy [J/(mol*K)]
        x--composition [array of mol frac]'''
    #check if input is in critical region
    pcrit = critp(x)[u'pcrit']
    if p > pcrit:
        raise RefpropinputError(u'p value input is critical condition')

    #calculate the properties (t and D)
    prop = flsh1(u'ps', p, s, x, 1)
    t = prop[u't']
    D = prop[u'D']

    #check if input is with liquid stage
    tbub = satp(p, x, 1)[u't']
    if t >= tbub:
        raise RefpropinputError(u'value input is not liquid condition')

    #check if input is with general refprop bounderies
    try:
        limitx(x, u'EOS', t, D, p)
    except RefpropWarning:
        pass

    #get remaining values
    prop = therm(t, D, x)

    #add q
    prop[u'q'] = -1

    #correct input values
    prop[u'p'] = p
    prop[u's'] = s

    #return full properties
    return prop


def psvap(p, s, x):
    u'''flsh1 calculations with boundery check, raise RefpropinputError when
    input is outside bounderies

    Inputs:
        p--pressure [kPa]
        s--entropy [J/(mol*K)]
        x--composition [array of mol frac]'''
    #check if input is in critical region (pressure)
    prop = critp(x)
    pcrit = prop[u'pcrit']
    tcrit = prop[u'tcrit']
    if p > pcrit:
        raise RefpropinputError(u'p value input is critical condition')

    #calculate the properties (t and D)
    prop = flsh1(u'ps', p, s, x, 2)
    t = prop[u't']
    D = prop[u'D']

    #check if input is in critical region (temperature)
    if t > tcrit:
        raise RefpropinputError(u'value input is critical condition')

    #check if input is with gas stage
    tdew = satp(p, x, 2)[u't']
    if t <= tdew:
        raise RefpropinputError(u'value input is not gas condition')

    #check if input is with general refprop bounderies
    try:
        limitx(x, u'EOS', t, D, p)
    except RefpropWarning:
        pass

    #get values
    prop = therm(t, D, x)

    #add q
    prop[u'q'] = 2

    #correct input values
    prop[u'p'] = p
    prop[u's'] = s

    #return full properties
    return prop


def ps2ph(p, s, x):
    u'''flsh2 calculations with boundery check, raise RefpropinputError when
    input is outside bounderies

    Inputs:
        p--pressure [kPa]
        s--entropy [J/(mol*K)]
        x--composition [array of mol frac]'''
    #check if input is in critical region
    pcrit = critp(x)[u'pcrit']
    if p > pcrit:
        raise RefpropinputError(u'p value input is critical condition')

    #calculate the properties
    prop = _abfl2(u'ps', p, s, x)
    D = prop[u'D']
    t = prop[u't']
    Dliq = prop[u'Dliq']
    Dvap = prop[u'Dvap']
    q = prop[u'q']
    xliq = prop[u'xliq']
    xvap = prop[u'xvap']

    #calculate properties at bubble point
    propliq = therm(t, Dliq, xliq)

    #calculate properties at cond. point
    propvap = therm(t, Dvap, xvap)

    #calculate e and h
    prop[u'e'] = (1 - q) * propliq[u'e'] + q * propvap[u'e']
    prop[u'h'] = (1 - q) * propliq[u'h'] + q * propvap[u'h']

    #check if input is within 2 phase stage
    tbub = prop[u'tbub']
    tdew = prop[u'tdew']
    if not tbub < t < tdew:
        raise RefpropinputError(u'value input is not 2-phase condition')

    #check if input is with general refprop bounderies
    try:
        limitx(x, u'EOS', t, D, p)
    except RefpropWarning:
        pass

    #return values
    return prop


def phliq(p, h, x):
    u'''flsh1 calculations with boundery check, raise RefpropinputError when
    input is outside bounderies

    Inputs:
        p--pressure [kPa]
        h--enthalpy [J/mol]
        x--composition [array of mol frac]'''
    #check if input is in critical region
    pcrit = critp(x)[u'pcrit']
    if p > pcrit:
        raise RefpropinputError(u'p value input is critical condition')

    #calculate the properties (t and D)
    prop = flsh1(u'ph', p, h, x, 1)
    t = prop[u't']
    D = prop[u'D']

    #check if input is with liquid stage
    tbub = satp(p, x, 1)[u't']
    if t >= tbub:
        raise RefpropinputError(u'value input is not liquid condition')

    #check if input is with general refprop bounderies
    try:
        limitx(x, u'EOS', t, D, p)
    except RefpropWarning:
        pass

    #get values
    prop = therm(t, D, x)

    #add q
    prop[u'q'] = -1

    #correct input values
    prop[u'p'] = p
    prop[u'h'] = h

    #return full properties
    return prop


def phvap(p, h, x):
    u'''flsh1 calculations with boundery check, raise RefpropinputError when
    input is outside bounderies

    Inputs:
        p--pressure [kPa]
        h--enthalpy [J/mol]
        x--composition [array of mol frac]'''
    #check if input is in critical region (pressure)
    prop = critp(x)
    pcrit = prop[u'pcrit']
    tcrit = prop[u'tcrit']
    if p > pcrit:
        raise RefpropinputError(u'p value input is critical condition')

    #calculate the properties (t and D)
    prop = flsh1(u'ph', p, h, x, 2)
    t = prop[u't']
    D = prop[u'D']

    #check if input is in critical region (temperature)
    if t > tcrit:
        raise RefpropinputError(u'value input is critical condition')

    #check if input is with gas stage
    tdew = satp(p, x, 2)[u't']
    if t <= tdew:
        raise RefpropinputError(u'value input is not gas condition')

    #check if input is with general refprop bounderies
    try:
        limitx(x, u'EOS', t, D, p)
    except RefpropWarning:
        pass

    #get values
    prop = therm(t, D, x)

    #add q
    prop[u'q'] = 2

    #correct input values
    prop[u'p'] = p
    prop[u'h'] = h

    #return full properties
    return prop


def ph2ph(p, h, x):
    u'''flsh2 calculations with boundery check, raise RefpropinputError when
    input is outside bounderies

    Inputs:
        p--pressure [kPa]
        h--enthalpy [J/mol]
        x--composition [array of mol frac]'''
    #check if input is in critical region
    pcrit = critp(x)[u'pcrit']
    if p > pcrit:
        raise RefpropinputError(u'p value input is critical condition')

    #calculate the properties
    prop = _abfl2(u'ph', p, h, x)
    D = prop[u'D']
    t = prop[u't']
    Dliq = prop[u'Dliq']
    Dvap = prop[u'Dvap']
    q = prop[u'q']
    xliq = prop[u'xliq']
    xvap = prop[u'xvap']

    #calculate properties at bubble point
    propliq = therm(t, Dliq, xliq)

    #calculate properties at cond. point
    propvap = therm(t, Dvap, xvap)

    #calculate e and h
    prop[u'e'] = (1 - q) * propliq[u'e'] + q * propvap[u'e']
    prop[u's'] = (1 - q) * propliq[u's'] + q * propvap[u's']

    #check if input is within 2 phase stage
    tbub = prop[u'tbub']
    tdew = prop[u'tdew']
    if not tbub < t < tdew:
        raise RefpropinputError(u'value input is not 2-phase condition')

    #check if input is with general refprop bounderies
    try:
        limitx(x, u'EOS', t, D, p)
    except RefpropWarning:
        pass

    #return values
    return prop


def setpath(path=None):
    u'''Set Directory to refprop root containing fluids and mixtures. Default
    value = '/usr/local/lib/refprop/'.
    This function must be called before
    SETUP if path is not default. Note, all fluids and mixtures to be filed
    under root/fluids and root/mixtures. Input in string format.
    '''
    global _purefld_rec, _setref_rec, _setaga_rec, _preos_rec
    global _gerg04_pre_rec, _gerg04_rec, _setmod_pre_rec, _setmod_rec
    global _setup_rec, _setktv_rec, _fixicomp, _fpath
    
    #reset fixicomp from def purefld()
    _fixicomp = 0

    #local declaration
    object_list = _Setuprecord.object_list

    if u'_purefld_rec' in object_list:
        _purefld_rec = None
    if u'_setref_rec' in object_list:
        _setref_rec = None
    if u'_setaga_rec' in object_list:
        _setaga_rec = None
    if u'_preos_rec' in object_list:
        _preos_rec = None
    if u'_setktv_rec' in object_list:
        _setktv_rec = None
    if u'_gerg04_pre_rec' in object_list:
        _gerg04_pre_rec = None
    if u'_gerg04_rec' in object_list:
        _gerg04_rec = None
    if u'_setmod_pre_rec' in object_list:
        _setmod_pre_rec = None
    if u'_setmod_rec' in object_list:
        _setmod_rec = None
    if u'_setup_rec' in object_list:
        _setup_rec = None

    #load refprop
    path = _loadfile(path)

    #set global path value
    _fpath = path


def _loadfile(fpath):
    global _rpsetup0_, _rpsetmod_, _rpgerg04_, _rpsetref_, _rpsetmix_, \
        _rpcritp_, _rptherm_, _rptherm0_, _rpresidual_, _rptherm2_, \
        _rptherm3_, _rpchempot_, _rppurefld_, _rpname_, _rpentro_, \
        _rpenthal_, _rpcvcp_, _rpcvcpk_, _rpgibbs_, _rpag_, _rppress_, \
        _rpdpdd_, _rpdpddk_, _rpdpdd2_, _rpdpdt_, _rpdpdtk_, _rpdddp_, \
        _rpdddt_, _rpdcdt_, _rpdcdt2_, _rpdhd1_, _rpfugcof_, _rpdbdt_, \
        _rpvirb_, _rpvirc_, _rpvird_, _rpvirba_, _rpvirca_, _rpsatt_, \
        _rpsatp_, _rpsatd_, _rpsath_, _rpsate_, _rpsats_, _rpcsatk_, \
        _rpdptsatk_, _rpcv2pk_, _rptprho_, _rptpflsh_, _rptdflsh_, \
        _rpthflsh_, _rptsflsh_, _rpteflsh_, _rppdflsh_, _rpphflsh_, \
        _rppsflsh_, _rppeflsh_, _rphsflsh_, _rpesflsh_, _rpdhflsh_, \
        _rpdsflsh_, _rpdeflsh_, _rptqflsh_, _rppqflsh_, _rpthfl1_, \
        _rptsfl1_, _rptefl1_, _rppdfl1_, _rpphfl1_, _rppsfl1_, _rppefl1_, \
        _rphsfl1_, _rpdhfl1_, _rpdsfl1_, _rpdefl1_, _rptpfl2_, _rpdhfl2_, \
        _rpdsfl2_, _rpdefl2_, _rpthfl2_, _rptsfl2_, _rptefl2_, _rptdfl2_, \
        _rppdfl2_, _rpphfl2_, _rppsfl2_, _rppefl2_, _rptqfl2_, _rppqfl2_, \
        _rpabfl2_, _rpinfo_, _rprmix2_, _rpxmass_, _rpxmole_, _rplimitx_, \
        _rplimitk_, _rplimits_, _rpqmass_, _rpqmole_, _rpwmoldll_, \
        _rpdielec_, _rpsurft_, _rpsurten_, _rpmeltt_, _rpmeltp_, _rpsublt_, \
        _rpsublp_, _rptrnprp_, _rpgetktv_, _rpgetmod_, _rpsetktv_, \
        _rpsetaga_, _rpunsetaga_, _rppreos_, _rpgetfij_, _rpb12_, \
        _rpexcess_, _rpphiderv_, _rpcstar_, _rpsetpath_, _rpfgcty_, _rpfpv_
    
    #set fpath  and filename
    if system() == u'Linux':
        if fpath == None:
            fpath = u'/usr/local/lib/refprop/'
        filename = fpath.rsplit(u'refprop/')[0] + u'librefprop.so'
        if not path.isfile(filename):
            raise RefpropError(u'can not find' + filename) 
        _rp = CDLL(unicode(filename), mode=RTLD_GLOBAL)
    elif system() == u'Windows':
        if fpath == None:
            #use the standard 2 windows options
            fpath=u'c:/program files/refprop/'
            #test 1
            try: listdir(fpath)
            except WindowsError:
                fpath=u'c:/program files (x86)/refprop/'
                #test 2
                listdir(fpath)
        filename = fpath + u'refprop.dll'
        if not path.isfile(filename):
            raise RefpropError(u'can not find' + filename) 
        _rp = windll.LoadLibrary(unicode(filename))

    #refprop functions
    if system() == u'Linux':
        (_rpsetup0_, _rpsetmod_, _rpgerg04_, _rpsetref_, _rpsetmix_,
         _rpcritp_, _rptherm_, _rptherm0_, _rpresidual_, _rptherm2_,
         _rptherm3_, _rpchempot_, _rppurefld_, _rpname_, _rpentro_,
         _rpenthal_, _rpcvcp_, _rpcvcpk_, _rpgibbs_, _rpag_, _rppress_,
         _rpdpdd_, _rpdpddk_, _rpdpdd2_, _rpdpdt_, _rpdpdtk_, _rpdddp_,
         _rpdddt_, _rpdcdt_, _rpdcdt2_, _rpdhd1_, _rpfugcof_, _rpdbdt_,
         _rpvirb_, _rpvirc_, _rpvird_, _rpvirba_, _rpvirca_, _rpsatt_,
         _rpsatp_, _rpsatd_, _rpsath_, _rpsate_, _rpsats_, _rpcsatk_,
         _rpdptsatk_, _rpcv2pk_, _rptprho_, _rptpflsh_, _rptdflsh_,
         _rpthflsh_, _rptsflsh_, _rpteflsh_, _rppdflsh_, _rpphflsh_,
         _rppsflsh_, _rppeflsh_, _rphsflsh_, _rpesflsh_, _rpdhflsh_,
         _rpdsflsh_, _rpdeflsh_, _rptqflsh_, _rppqflsh_, _rpthfl1_,
         _rptsfl1_, _rptefl1_, _rppdfl1_, _rpphfl1_, _rppsfl1_, _rppefl1_,
         _rphsfl1_, _rpdhfl1_, _rpdsfl1_, _rpdefl1_, _rptpfl2_, _rpdhfl2_,
         _rpdsfl2_, _rpdefl2_, _rpthfl2_, _rptsfl2_, _rptefl2_, _rptdfl2_,
         _rppdfl2_, _rpphfl2_, _rppsfl2_, _rppefl2_, _rptqfl2_, _rppqfl2_,
         _rpabfl2_, _rpinfo_, _rprmix2_, _rpxmass_, _rpxmole_, _rplimitx_,
         _rplimitk_, _rplimits_, _rpqmass_, _rpqmole_, _rpwmoldll_,
         _rpdielec_, _rpsurft_, _rpsurten_, _rpmeltt_, _rpmeltp_, _rpsublt_,
         _rpsublp_, _rptrnprp_, _rpgetktv_, _rpgetmod_, _rpsetktv_,
         _rpsetaga_, _rpunsetaga_, _rppreos_, _rpgetfij_, _rpb12_,
         _rpexcess_, _rpphiderv_, _rpcstar_, _rpsetpath_, _rpfgcty_,
         _rpfpv_) = \
        (_rp.setup0_, _rp.setmod_, _rp.gerg04_, _rp.setref_, _rp.setmix_,
         _rp.critp_, _rp.therm_, _rp.therm0_, _rp.residual_, _rp.therm2_,
         _rp.therm3_, _rp.chempot_, _rp.purefld_, _rp.name_, _rp.entro_,
         _rp.enthal_, _rp.cvcp_, _rp.cvcpk_, _rp.gibbs_, _rp.ag_, _rp.press_,
         _rp.dpdd_, _rp.dpddk_, _rp.dpdd2_, _rp.dpdt_, _rp.dpdtk_, _rp.dddp_,
         _rp.dddt_, _rp.dcdt_, _rp.dcdt2_, _rp.dhd1_, _rp.fugcof_, _rp.dbdt_,
         _rp.virb_, _rp.virc_, _rp.vird_, _rp.virba_, _rp.virca_, _rp.satt_,
         _rp.satp_, _rp.satd_, _rp.sath_, _rp.sate_, _rp.sats_, _rp.csatk_,
         _rp.dptsatk_, _rp.cv2pk_, _rp.tprho_, _rp.tpflsh_, _rp.tdflsh_,
         _rp.thflsh_, _rp.tsflsh_, _rp.teflsh_, _rp.pdflsh_, _rp.phflsh_,
         _rp.psflsh_, _rp.peflsh_, _rp.hsflsh_, _rp.esflsh_, _rp.dhflsh_,
         _rp.dsflsh_, _rp.deflsh_, _rp.tqflsh_, _rp.pqflsh_, _rp.thfl1_,
         _rp.tsfl1_, _rp.tefl1_, _rp.pdfl1_, _rp.phfl1_, _rp.psfl1_, _rp.pefl1_,
         _rp.hsfl1_, _rp.dhfl1_, _rp.dsfl1_, _rp.defl1_, _rp.tpfl2_, _rp.dhfl2_,
         _rp.dsfl2_, _rp.defl2_, _rp.thfl2_, _rp.tsfl2_, _rp.tefl2_, _rp.tdfl2_,
         _rp.pdfl2_, _rp.phfl2_, _rp.psfl2_, _rp.pefl2_, _rp.tqfl2_, _rp.pqfl2_,
         _rp.abfl2_, _rp.info_, _rp.rmix2_, _rp.xmass_, _rp.xmole_, _rp.limitx_,
         _rp.limitk_, _rp.limits_, _rp.qmass_, _rp.qmole_, _rp.wmoldll_,
         _rp.dielec_, _rp.surft_, _rp.surten_, _rp.meltt_, _rp.meltp_, _rp.sublt_,
         _rp.sublp_, _rp.trnprp_, _rp.getktv_, _rp.getmod_, _rp.setktv_,
         _rp.setaga_, _rp.unsetaga_, _rp.preos_, _rp.getfij_, _rp.b12_,
         _rp.excess_, _rp.phiderv_, _rp.cstar_, _rp.setpath_, _rp.fgcty_,
         _rp.fpv_)
    
    elif system() == u'Windows':
        (_rpsetup0_, _rpsetmod_, _rpgerg04_, _rpsetref_, _rpsetmix_,
         _rpcritp_, _rptherm_, _rptherm0_, _rpresidual_, _rptherm2_,
         _rptherm3_, _rpchempot_, _rppurefld_, _rpname_, _rpentro_,
         _rpenthal_, _rpcvcp_, _rpcvcpk_, _rpgibbs_, _rpag_, _rppress_,
         _rpdpdd_, _rpdpddk_, _rpdpdd2_, _rpdpdt_, _rpdpdtk_, _rpdddp_,
         _rpdddt_, _rpdhd1_, _rpfugcof_, _rpdbdt_,
         _rpvirb_, _rpvirc_, _rpvirba_, _rpvirca_, _rpsatt_,
         _rpsatp_, _rpsatd_, _rpsath_, _rpsate_, _rpsats_, _rpcsatk_,
         _rpdptsatk_, _rpcv2pk_, _rptprho_, _rptpflsh_, _rptdflsh_,
         _rpthflsh_, _rptsflsh_, _rpteflsh_, _rppdflsh_, _rpphflsh_,
         _rppsflsh_, _rppeflsh_, _rphsflsh_, _rpesflsh_, _rpdhflsh_,
         _rpdsflsh_, _rpdeflsh_, _rptqflsh_, _rppqflsh_,
         _rppdfl1_, _rpphfl1_, _rppsfl1_,
         _rpinfo_, _rpxmass_, _rpxmole_, _rplimitx_,
         _rplimitk_, _rplimits_, _rpqmass_, _rpqmole_, _rpwmoldll_,
         _rpdielec_, _rpsurft_, _rpsurten_, _rpmeltt_, _rpmeltp_, _rpsublt_,
         _rpsublp_, _rptrnprp_, _rpgetktv_, _rpsetktv_,
         _rpsetaga_, _rpunsetaga_, _rppreos_, _rpgetfij_, _rpb12_,
         _rpcstar_, _rpsetpath_, _rpfgcty_,
         _rpfpv_) = \
        (_rp.SETUPdll, _rp.SETMODdll, _rp.GERG04dll, _rp.SETREFdll,
         _rp.SETMIXdll, _rp.CRITPdll, _rp.THERMdll, _rp.THERM0dll,
         _rp.RESIDUALdll, _rp.THERM2dll, _rp.THERM3dll, _rp.CHEMPOTdll,
         _rp.PUREFLDdll, _rp.NAMEdll, _rp.ENTROdll, _rp.ENTHALdll, _rp.CVCPdll,
         _rp.CVCPKdll, _rp.GIBBSdll, _rp.AGdll, _rp.PRESSdll, _rp.DPDDdll,
         _rp.DPDDKdll, _rp.DPDD2dll, _rp.DPDTdll, _rp.DPDTKdll, _rp.DDDPdll,
         _rp.DDDTdll, _rp.DHD1dll, _rp.FUGCOFdll,
         _rp.DBDTdll, _rp.VIRBdll, _rp.VIRCdll, _rp.VIRBAdll,
         _rp.VIRCAdll, _rp.SATTdll, _rp.SATPdll, _rp.SATDdll, _rp.SATHdll,
         _rp.SATEdll, _rp.SATSdll, _rp.CSATKdll, _rp.DPTSATKdll, _rp.CV2PKdll,
         _rp.TPRHOdll, _rp.TPFLSHdll, _rp.TDFLSHdll, _rp.THFLSHdll,
         _rp.TSFLSHdll, _rp.TEFLSHdll, _rp.PDFLSHdll, _rp.PHFLSHdll, _rp.PSFLSHdll,
         _rp.PEFLSHdll, _rp.HSFLSHdll, _rp.ESFLSHdll, _rp.DHFLSHdll,
         _rp.DSFLSHdll, _rp.DEFLSHdll, _rp.TQFLSHdll, _rp.PQFLSHdll,
         _rp.PDFL1dll, _rp.PHFL1dll,
         _rp.PSFL1dll,
         _rp.INFOdll, _rp.XMASSdll, _rp.XMOLEdll,
         _rp.LIMITXdll, _rp.LIMITKdll, _rp.LIMITSdll, _rp.QMASSdll, _rp.QMOLEdll,
         _rp.WMOLdll, _rp.DIELECdll, _rp.SURFTdll, _rp.SURTENdll, _rp.MELTTdll,
         _rp.MELTPdll, _rp.SUBLTdll, _rp.SUBLPdll, _rp.TRNPRPdll, _rp.GETKTVdll,
         _rp.SETKTVdll, _rp.SETAGAdll, _rp.UNSETAGAdll,
         _rp.PREOSdll, _rp.GETFIJdll, _rp.B12dll,
         _rp.CSTARdll, _rp.SETPATHdll, _rp.FGCTYdll, _rp.FPVdll)
    #set path for refprop
    _hpth.value = fpath.encode(u'ascii')
    _rpsetpath_(byref(_hpth), c_long(255))

    return fpath

#REFPROP functions
def setup(hrf, *hfld, **_3to2kwargs):
    if 'hfmix' in _3to2kwargs: hfmix = _3to2kwargs['hfmix']; del _3to2kwargs['hfmix']
    else: hfmix = u'HMX.BNC'
    u'''Define models and initialize arrays.
    A call to this routine is required.

    Inputs 'in string format':
        hrf - reference state for thermodynamic calculations
            'def' : Default reference state as specified in fluid file is
                applied to each pure component.
            'nbs' : h,s = 0 at pure component normal boiling point(s).
            'ash' : h,s = 0 for sat liquid at -40 C (ASHRAE convention)
            'iir' : h = 200, s = 1.0 for sat liq at 0 C (IIR convention) Other
                choises are possible but require a separate call to SETREF
        *hfld - file names specifying fluid mixture components
            select from user fluid.FLD and mixture.MIX files at root directory
            input without extention.
            Pseudo-Pure Fluids (PPF) files are required to have the extention
            included
        hfmix--file name [character*255] containing parameters for the binary
            mixture model'''
    global _nc_rec, _fpath, _gerg04_pre_rec, _setmod_pre_rec, _setup_rec
    global _setmod_rec, _gerg04_rec, _setref_rec, _purefld_rec, _setktv_rec
    global _setaga_rec, _preos_rec, _setupprop
    _inputerrorcheck(locals())

    #define setup record for Fluidmodel
    _setup_rec = _Setuprecord(copy(locals()), u'_setup_rec')

    #empty global setup storage for new population
    _setupprop = {}

    #load refprop shared library
    if _fpath == u'':
        setpath()

    fluidname = u''
    listhfld = []

    #create listing of input *hfld (in either list format or *arg string format)
    for each in hfld:
        if each.__class__ is list:
            for other in each:
                listhfld.append(other.upper())
        elif each.__class__ is unicode:
            listhfld.append(each.upper())
    
    #create RP input format with file directory structure and file extention
    for each in listhfld:
        if _fluidextention()[_fpath + u'fluids/'].__contains__(each):
            if each[-4:] == u'.PPF':
                fluidname += _fpath + u'fluids/' + each + u'|'
            else: fluidname += _fpath + u'fluids/' + each + u'.FLD|'
        elif _fluidextention()[_fpath + u'mixtures/'].__contains__(each):
            fluidname += _fpath + u'mixtures/' + each + u'.MIX|'

    nc = len(listhfld)
    _nc_rec = _Setuprecord(nc, u'_nc_rec')

    if u'_preos_rec' in _Setuprecord.object_list:
        _preos_rec = None
    if u'_setaga_rec' in _Setuprecord.object_list:
        _setaga_rec = None
    if u'_setref_rec' in _Setuprecord.object_list:
        _setref_rec = None
    if u'_setktv_rec' in _Setuprecord.object_list:
        _setktv_rec = None
    if u'_purefld_rec' in _Setuprecord.object_list:
        _purefld_rec = None

    #determine if SETMOD needs to be called
    if u'_setmod_pre_rec' in _Setuprecord.object_list:
        #call setmod
        ierr, herr = _setmod(nc, _setmod_pre_rec.record[u'htype'],
                             _setmod_pre_rec.record[u'hmix'],
                             _setmod_pre_rec.record[u'hcomp'])

        _prop(ierr = ierr, herr = herr, defname = u'_setmod')
    
    #reset SETMOD from record
    elif u'_setmod_rec' in _Setuprecord.object_list:
        _setmod_rec = None
    
    #determine if GERG04 needs to be called
    if u'_gerg04_pre_rec' in _Setuprecord.object_list:
        ierr, herr = _gerg04(nc, _gerg04_pre_rec.record[u'ixflag'])

        _prop(ierr = ierr, herr = herr, defname = u'_gerg04')

    #reset GERG04 from record
    elif u'_gerg04_rec' in _Setuprecord.object_list:
        _gerg04_rec = None
    
    #determine standard mix (handled by setmix) or user defined mixture
    #(handled by setupdll)
    if fluidname.__contains__(u'.MIX|'):
        if len(listhfld) > 1:
            raise RefpropinputError (u'too many standard mixture input, ' +
            u'can only select one')
        for item in listhfld:
            mix = unicode(item)
        return _setmix(mix, hrf, hfmix)
    else:
        if u'hmxnme' in _setupprop:
            _setupprop.__delitem__(u'hmxnme')
        _setupprop[u'hfld'], _setupprop[u'nc'] = listhfld, nc
        _setupprop[u'hrf'], _setupprop[u'hfmix'] = hrf.upper(), hfmix
        return _setup0(nc, fluidname, hfmix, hrf)


def setmod(htype=u'NBS', hmix=u'NBS', *hcomp):
    u'''Set model(s) other than the NIST-recommended ('NBS') ones.

    This subroutine must be called before SETUP; it need not be called at
    all if the default (NIST-recommended) models are desired.

    inputs 'in string format':
        htype - flag indicating which models are to be set [character*3]:
            'EOS':  equation of state for thermodynamic properties
            'ETA':  viscosity
            'TCX':  thermal conductivity
            'STN':  surface tension
            'NBS':  reset all of the above model types and all subsidiary
                component models to 'NBS'; values of hmix and hcomp are ignored
        hmix--mixture model to use for the property specified in htype
            [character*3]:
            ignored if number of components = 1
            some allowable choices for hmix:
                'NBS':  use NIST recommendation for specified fluid/mixture
                'HMX':  mixture Helmholtz model for thermodynamic properties
                'ECS':  extended corresponding states for viscosity or therm. cond.
                'STX':  surface tension mixture model
        hcomp--component model(s) to use for property specified in htype
            [array (1..nc) of character*3]:
                'NBS':  NIST recommendation for specified fluid/mixture
            some allowable choices for an equation of state:
                'FEQ':  Helmholtz free energy model
                'BWR':  pure fluid modified Benedict-Webb-Rubin (MBWR)
                'ECS':  pure fluid thermo extended corresponding states
            some allowable choices for viscosity:
                'ECS':  extended corresponding states (all fluids)
                'VS1':  the 'composite' model for R134a, R152a, NH3, etc.
                'VS2':  Younglove-Ely model for hydrocarbons
                'VS4':  Generalized friction theory of Quinones-Cisneros and
                    Deiters
                'VS5':  Chung et al. (1988) predictive model
            some allowable choices for thermal conductivity:
                'ECS':  extended corresponding states (all fluids)
                'TC1':  the 'composite' model for R134a, R152a, etc.
                'TC2':  Younglove-Ely model for hydrocarbons
                'TC5':  Chung et al. (1988) predictive model
            some allowable choices for surface tension:
                'ST1':  surface tension as f(tau); tau = 1 - T/Tc'''
    global _setmod_pre_rec
    _inputerrorcheck(locals())

    #hcomp correction
    #no input for hcomp
    if len(hcomp) == 0:
        hcomp = []
    #list input for hcomp
    elif hcomp[0].__class__ is list:
        hcomp = hcomp[0]
    #str's input for hcomp
    else:
        hcomp = [each for each in hcomp]

    #define setup record for FluidModel
    _setmod_pre_rec = _Setuprecord(copy(locals()), u'_setmod_pre_rec')


def gerg04(ixflag=0):
    u'''set the pure model(s) to those used by the GERG 2004 formulation.

    This subroutine must be called before SETUP; it need not be called
    at all if the default (NIST-recommended) models are desired.
    To turn off the GERG settings, call this routine again with iflag=0,
    and then call the SETUP routine to reset the parameters of the equations
    of state.

    inputs:
        ixflag--set to 1 to load the GERG 2004 equations, set to 0 for defaults'''
    global _gerg04_pre_rec
    _inputerrorcheck(locals())

    _gerg04_pre_rec = _Setuprecord(copy(locals()), u'_gerg04_pre_rec')

    if not (ixflag == 0 or ixflag == 1):
        raise RefpropinputError(u'ixflag value for function "gerg04" ' +
                                 u'should either be 0 (default) or 1')


#refprop functions
def _setup0(nc, fluidname, hfmix, hrf):
        global _fpath
        _nc.value = nc
        _hfld.value = fluidname.encode(u'ascii')
        if hfmix == u'HMX.BNC':
            _hfmix.value = (_fpath + u'fluids/HMX.BNC').encode(u'ascii')
        else:
            _hfmix.value = hfmix.encode(u'ascii')
        _hrf.value = hrf.upper().encode(u'ascii')

        _rpsetup0_(byref(_nc), byref(_hfld), byref(_hfmix), byref(_hrf),
                   byref(_ierr), byref(_herr), c_long(10000), c_long(255),
                   c_long(3), c_long(255))
                     

        return _prop(ierr = _ierr.value, herr = _herr.value, defname = u'_setup0')


def _setmod(nc, htype, hmix, hcomp):
    global _setmod_rec, _setmod_pre_rec, _setupprop

    #verify multiple model calls
    _checksetupmodel(u'setmod')

    #define setup record for FluidModel
    if u'_setmod_pre_rec' in _Setuprecord.object_list:
        if htype.upper() == u'NBS':
            if u'_setmod_rec' in _Setuprecord.object_list:
                _setmod_rec = None
            if u'setmod' in _setupprop:
                _setupprop.__delitem__(u'setmod')
        else:
            _setmod_rec = _Setuprecord(_setmod_pre_rec.record, u'_setmod_rec')
            if nc == 1:
                _setmod_rec.record.__delitem__(u'hmix')
            _setupprop[u'setmod'] = _setmod_rec.record

        _setmod_pre_rec = None

    _nc.value = nc
    _htype.value = htype.encode(u'ascii')
    _hmix.value = hmix.encode(u'ascii')
    for each in xrange(len(hcomp)):
        _hcomp[each].value = hcomp[each].encode(u'ascii')
    
    _rpsetmod_(byref(_nc), byref(_htype), byref(_hmix), byref(_hcomp),
               byref(_ierr), byref(_herr), c_long(3), c_long(3), c_long(3),
               c_long(255))
    
    return _ierr.value, _herr.value


def _gerg04(nc, ixflag):
    global _gerg04_rec, _gerg04_pre_rec, _setupprop

    #verify multiple model calls
    _checksetupmodel(u'gerg04')

    #define setup record for FluidModel
    if u'_gerg04_pre_rec' in _Setuprecord.object_list:
        if ixflag == 1:
            _gerg04_rec = _Setuprecord(_gerg04_pre_rec.record, u'_gerg04_rec')
            _setupprop[u'gerg04'] = _gerg04_pre_rec.record
        if ixflag == 0:
            if u'_gerg04_rec' in _Setuprecord.object_list:
                _gerg04_rec = None
            if u'gerg04' in _setupprop:
                _setupprop.__delitem__(u'gerg04')
        _gerg04_pre_rec = None

    if ixflag == 1:
        _nc.value = nc
        _ixflag.value = ixflag
        
        _rpgerg04_(byref(_nc), byref(_ixflag), byref(_ierr), byref(_herr),
                   c_long(255))
        
        return _ierr.value, _herr.value
    #system tweak as refprop call gerg04(ixflag=0) does not reset properly
    elif ixflag == 0:
        return 0, u''


def setref(hrf=u'DEF', ixflag=1, x0=[1], h0=0, s0=0, t0=273, p0=100):
    u'''set reference state enthalpy and entropy

    This subroutine must be called after SETUP; it need not be called at all
    if the reference state specified in the call to SETUP is to be used.

    inputs:
        hrf--reference state for thermodynamic calculations [character*3]
            'NBP':  h,s = 0 at normal boiling point(s)
            'ASH':  h,s = 0 for sat liquid at -40 C (ASHRAE convention)
            'IIR':  h = 200, s = 1.0 for sat liq at 0 C (IIR convention)
            'DEF':  default reference state as specified in fluid file is
                applied to each component (ixflag = 1 is used)
            'OTH':  other, as specified by h0, s0, t0, p0 (real gas state)
            'OT0':  other, as specified by h0, s0, t0, p0 (ideal gas state)
            '???':  change hrf to the current reference state and exit.
        ixflag--composition flag:
            1 = ref state applied to pure components
            2 = ref state applied to mixture icomp
        following input has meaning only if ixflag = 2
            x0--composition for which h0, s0 apply; list(1:nc) [mol frac]
                this is useful for mixtures of a predefined composition, e.g.
                refrigerant blends such as R410A
        following inputs have meaning only if hrf = 'OTH'
            h0--reference state enthalpy at t0,p0 {icomp} [J/mol]
            s0--reference state entropy at t0,p0 {icomp} [J/mol-K]
            t0--reference state temperature [K]
                t0 = -1 indicates saturated liquid at normal boiling point
                    (bubble point for a mixture)
            p0--reference state pressure [kPa]
                p0 = -1 indicates saturated liquid at t0 {and icomp}
                p0 = -2 indicates saturated vapor at t0 {and icomp}'''
    _inputerrorcheck(locals())
    global _setref_rec, _setupprop

    #define setup record for FluidModel
    if hrf.upper() != u'DEF':
        _setref_rec = _Setuprecord(copy(locals()), u'_setref_rec')
    elif u'setref_rec' in _Setuprecord.object_list:
        _setref_rec = None

    for each in xrange(_maxcomps): _x0[each] = 0
    for each in xrange(len(x0)): _x0[each] = x0[each]
    _hrf.value = hrf.upper().encode(u'ascii')
    _ixflag.value = ixflag
    _h0.value, _s0.value, _t0.value, _p0.value = h0, s0, t0, p0
    
    _rpsetref_(byref(_hrf), byref(_ixflag), byref(_x0), byref(_h0),
               byref(_s0), byref(_t0), byref(_p0), byref(_ierr),
               byref(_herr), c_long(3), c_long(255))
    
    if (hrf.upper() != u'DEF' and hrf.upper() != u'NBP' and hrf.upper() != u'ASH'
         and hrf.upper() != u'IIR'):
        href = {}
        if hrf == u'???':
            href[u'hrf'] = [_setupprop[u'setref'][u'hrf'][0], hrf]
            if u'ixflag' in _setupprop[u'setref']:
                href[u'ixflag'] = _setupprop[u'setref'][u'ixflag']
            if u'x' in _setupprop[u'setref']:
                href[u'x0'] = _setupprop[u'setref'][u'x0']
            if u'h0' in _setupprop[u'setref']:
                href[u'h0'] = _setupprop[u'setref'][u'h0']
            if u's0' in _setupprop[u'setref']:
                href[u's0'] = _setupprop[u'setref'][u's0']
            if u't0' in _setupprop[u'setref']:
                href[u't0'] = _setupprop[u'setref'][u't0']
            if u'p0' in _setupprop[u'setref']:
                href[u'p0'] = _setupprop[u'setref'][u'p0']
        else:
            href[u'hrf'] = [hrf.upper()]
            href[u'ixflag'] = ixflag
            if ixflag == 2: href[u'x0'] = x0
            if hrf.upper() == u'OTH':
                href[u'h0'] = h0
                href[u's0'] = s0
                href[u't0'] = t0
                href[u'p0'] = p0
        _setupprop[u'setref'] = href
    elif hrf.upper() != u'DEF':
        _setupprop[u'setref'] = {u'hrf':[hrf.upper()]}
    else:
        if u'setref' in _setupprop:
            _setupprop.__delitem__(u'setref')

    return _prop(ierr = _ierr.value, herr = _herr.value, defname = u'setref')
    

def _setmix(hmxnme, hrf, hfmix):
    global _nc_rec, _setupprop
    _inputerrorcheck(locals())
    _hmxnme.value = (hmxnme + u'.MIX').encode(u'ascii')
    _hfmix.value = hfmix.encode(u'ascii')
    _hrf.value = hrf.upper().encode(u'ascii')

    _rpsetmix_(byref(_hmxnme), byref(_hfmix), byref(_hrf), byref(_nc),
               byref(_hfld), _x, byref(_ierr), byref(_herr), c_long(255),
               c_long(255), c_long(3), c_long(10000), c_long(255))
    
    hfld = []
    _nc_rec = _Setuprecord(_nc.value, u'_nc_rec')
    for each in xrange(_nc.value):
        hfld.append(_name(each + 1))

    x = normalize([_x[each] for each in xrange(_nc.value)])[u'x']
    _setupprop[u'hmxnme'], _setupprop[u'hrf'] = hmxnme, hrf.upper()
    _setupprop[u'nc'], _setupprop[u'hfld'] = _nc.value, hfld
    _setupprop[u'hfmix'] = hfmix
    return _prop(x = x, ierr = _ierr.value, herr = _herr.value,
                  defname = u'setmix')


def critp(x):
    u'''critical parameters as a function of composition

    input:
        x--composition [list of mol frac]
    outputs:
        tcrit--critical temperature [K]
        pcrit--critical pressure [kPa]
        Dcrit--critical density [mol/L]'''

    _inputerrorcheck(locals())
    for each in xrange(len(x)): _x[each] = x[each]
    
    _rpcritp_(_x, byref(_tcrit), byref(_pcrit), byref(_Dcrit),
              byref(_ierr), byref(_herr), c_long(255))
    
    return _prop(x = x, tcrit = _tcrit.value, pcrit = _pcrit.value,
                  Dcrit = _Dcrit.value, ierr = _ierr.value, herr = _herr.value,
                  defname = u'critp')
                  

def therm(t, D, x):
    u'''Compute thermal quantities as a function of temperature, density and
    compositions using core functions (Helmholtz free energy, ideal gas heat
    capacity and various derivatives and integrals). Based on derivations in
    Younglove & McLinden, JPCRD 23 #5, 1994, Appendix A for
    pressure-explicit equations (e.g. MBWR) and c  Baehr & Tillner-Roth,
    Thermodynamic Properties of Environmentally Acceptable Refrigerants,
    Berlin:  Springer-Verlag (1995) for Helmholtz-explicit equations (e.g.
    FEQ).

    inputs:
        t--temperature [K]
        D--molar density [mol/L]
        x--composition [array of mol frac]
    outputs:
        p--pressure [kPa]
        e--internal energy [J/mol]
        h--enthalpy [J/mol]
        s--entropy [J/mol-K]
        cv--isochoric heat capacity [J/mol-K]
        cp--isobaric heat capacity [J/mol-K]
        w--speed of sound [m/s]
        hjt--isenthalpic Joule-Thompson coefficient [K/kPa]'''
    _inputerrorcheck(locals())
    _t.value, _D.value = t, D
    for each in xrange(len(x)): _x[each] = x[each]

    _rptherm_(byref(_t), byref(_D), _x, byref(_p), byref(_e), byref(_h),
              byref(_s), byref(_cv), byref(_cp), byref(_w), byref(_hjt))

    return _prop(x = x, D = D, t = t, p = _p.value, e = _e.value, h = _h.value,
                  s = _s.value, cv = _cv.value, cp = _cp.value, w = _w.value,
                  hjt = _hjt.value)


def therm0(t, D, x):
    u'''Compute ideal gas thermal quantities as a function of temperature,
    density and compositions using core functions.

    This routine is the same as THERM, except it only calculates ideal gas
    properties (Z=1) at any temperature and density

    inputs:
        t--temperature [K]
        D--molar density [mol/L]
        x--composition [array of mol frac]
    outputs:
        p--pressure [kPa]
        e--internal energy [J/mol]
        h--enthalpy [J/mol]
        s--entropy [J/mol-K]
        cv--isochoric heat capacity [J/mol-K]
        cp--isobaric heat capacity [J/mol-K]
        w--speed of sound [m/s]
        A--Helmholtz energy [J/mol]
        G--Gibbs free energy [J/mol]'''
    _inputerrorcheck(locals())
    _t.value = t
    _D.value = D
    for each in xrange(len(x)): _x[each] = x[each]

    _rptherm0_(byref(_t), byref(_D), _x, byref(_p), byref(_e), byref(_h),
              byref(_s), byref(_cv), byref(_cp), byref(_w), byref(_A),
              byref(_G))
    
    return _prop(x = x, D = D, t = t, p = _p.value, e = _e.value, h = _h.value,
                  s = _s.value, cv = _cv.value, cp = _cp.value, w = _w.value,
                  A = _A.value, G = _G.value)


def residual (t, D, x):
    u'''compute the residual quantities as a function of temperature, density,
    and compositions (where the residual is the property minus the ideal gas
    portion).

    inputs:
        t--temperature [K]
        D--molar density [mol/L]
        x--composition [array of mol frac]
    outputs:
        pr--residual pressure [kPa]  (p-rho*R*T)
        er--residual internal energy [J/mol]
        hr--residual enthalpy [J/mol]
        sr--residual entropy [J/mol-K]
        Cvr--residual isochoric heat capacity [J/mol-K]
        Cpr--residual isobaric heat capacity [J/mol-K]
        Ar--residual Helmholtz energy [J/mol]
        Gr--residual Gibbs free energy [J/mol]'''
    _inputerrorcheck(locals())
    _t.value = t
    _D.value = D
    for each in xrange(len(x)): _x[each] = x[each]

    _rpresidual_(byref(_t), byref(_D), _x, byref(_pr), byref(_er),
                 byref(_hr), byref(_sr), byref(_cvr), byref(_cpr),
                 byref(_Ar), byref(_Gr))
    
    return _prop(x = x, D = D, t = t, pr = _pr.value, er = _er.value,
            hr = _hr.value, sr = _sr.value, cvr = _cvr.value, cpr = _cpr.value,
            Ar = _Ar.value, Gr = _Gr.value)


def therm2(t, D, x):
    u'''Compute thermal quantities as a function of temperature, density and
    compositions using core functions (Helmholtz free energy, ideal gas heat
    capacity and various derivatives and integrals).

    This routine is the same as THERM, except that additional properties are
    calculated

    inputs:
        t--temperature [K]
        D--molar density [mol/L]
        x--composition [array of mol frac]
    outputs:
        p--pressure [kPa]
        e--internal energy [J/mol]
        h--enthalpy [J/mol]
        s--entropy [J/mol-K]
        cv--isochoric heat capacity [J/mol-K]
        cp--isobaric heat capacity [J/mol-K]
        w--speed of sound [m/s]
        Z--compressibility factor (= PV/RT) [dimensionless]
        hjt--isenthalpic Joule-Thompson coefficient [K/kPa]
        A--Helmholtz energy [J/mol]
        G--Gibbs free energy [J/mol]
        xkappa--isothermal compressibility (= -1/V dV/dp = 1/D dD/dp) [1/kPa]
        beta--volume expansivity (= 1/V dV/dt = -1/D dD/dt) [1/K]
        dpdD--derivative dP/dD [kPa-L/mol]
        d2pdD2--derivative d^2p/dD^2 [kPa-L^2/mol^2]
        dpdt--derivative dp/dt [kPa/K]
        dDdt--derivative dD/dt [mol/(L-K)]
        dDdp--derivative dD/dp [mol/(L-kPa)]
        spare1 to 4--space holders for possible future properties'''
    _inputerrorcheck(locals())
    _t.value = t
    _D.value = D
    for each in xrange(len(x)): _x[each] = x[each]

    _rptherm2_(byref(_t), byref(_D), _x, byref(_p), byref(_e), byref(_h),
                byref(_s), byref(_cv), byref(_cp), byref(_w), byref(_Z),
                byref(_hjt), byref(_A), byref(_G), byref(_xkappa),
                byref(_beta), byref(_dpdD), byref(_d2pdD2), byref(_dpdt),
                byref(_dDdt), byref(_dDdp), byref(_spare1), byref(_spare2),
                byref(_spare3), byref(_spare4))

    return _prop(x = x, D = D, t = t, p = _p.value, e = _e.value, h = _h.value,
            s = _s.value, cv = _cv.value, cp = _cp.value, w = _w.value,
            Z = _Z.value, hjt = _hjt.value, A = _A.value, G = _G.value,
            xkappa = _xkappa.value, beta = _beta.value, dpdD = _dpdD.value,
            d2pdD2 = _d2pdD2.value, dpdt = _dpdt.value, dDdt = _dDdt.value,
            dDdp = _dDdp.value)


def therm3(t, D, x):
    u'''Compute miscellaneous thermodynamic properties

    inputs:
        t--temperature [K]
        D--molar density [mol/L]
        x--composition [array of mol frac]
    outputs:
        xkappa--Isothermal compressibility
        beta--Volume expansivity
        xisenk--Isentropic expansion coefficient
        xkt--Isothermal expansion coefficient
        betas--Adiabatic compressibility
        bs--Adiabatic bulk modulus
        xkkt--Isothermal bulk modulus
        thrott--Isothermal throttling coefficient
        pint--Internal pressure
        spht--Specific heat input'''
    _inputerrorcheck(locals())
    _t.value = t
    _D.value = D
    for each in xrange(len(x)): _x[each] = x[each]
    
    _rptherm3_(byref(_t), byref(_D), _x, byref(_xkappa), byref(_beta),
                byref(_xisenk), byref(_xkt), byref(_betas), byref(_bs),
                byref(_xkkt), byref(_thrott), byref(_pint), byref(_spht))
    
    return _prop(x = x, D = D, t = t, xkappa = _xkappa.value,
        beta = _beta.value, xisenk = _xisenk.value, xkt = _xkt.value,
        betas = _betas.value, bs = _bs.value, xkkt = _xkkt.value,
        thrott = _thrott.value, pint = _pint.value, spht = _spht.value)


def fpv(t, D, p, x):
    u'''Compute the supercompressibility factor, Fpv.

    inputs:
        t--temperature [K]
        D--molar density [mol/L]
        p--pressure [kPa]
        x--composition [array of mol frac]
    outputs:
        Fpv--sqrt[Z(60 F, 14.73 psia)/Z(T,P)].'''
    #odd either t, d or t, p should be sufficient?
    _inputerrorcheck(locals())
    _t.value = t
    _D.value = D
    _p.value = p
    for each in xrange(len(x)): _x[each] = x[each]
    
    _rpfpv_(byref(_t), byref(_D), byref(_p), _x, byref(_Fpv))
    
    return _prop(x = x, D = D, t = t, p = p, Fpv = _Fpv.value)


def chempot(t, D, x):
    u'''Compute the chemical potentials for each of the nc components of a
    mixture

    inputs:
        t--temperature [K]
        D--molar density [mol/L]
        x--composition [array of mol frac]
    outputs:
        u--array (1..nc) of the chemical potentials [J/mol].'''
    _inputerrorcheck(locals())

    _t.value = t
    _D.value = D
    for each in xrange(len(x)): _x[each] = x[each]
    
    _rpchempot_(byref(_t), byref(_D), _x, _u, byref(_ierr), byref(_herr),
                 c_long(255))
    
    return _prop(x = x, D = D, t = t, ierr = _ierr.value, herr = _herr.value,
        u = [_u[each] for each in xrange(_nc_rec.record)], defname = u'chempot')
            

def purefld(icomp=0):
    u'''Change the standard mixture setup so that the properties of one fluid
    can be calculated as if SETUP had been called for a pure fluid. Calling
    this routine will disable all mixture calculations. To reset the mixture
    setup, call this routine with icomp=0.

    inputs:
        icomp--fluid number in a mixture to use as a pure fluid'''
    global _purefld_rec

    _inputerrorcheck(locals())

    #define setup record for FluidModel
    if icomp != 0:
        _purefld_rec = _Setuprecord(copy(locals()), u'_purefld_rec')
    else:
        #del record
        if u'_purefld_rec' in _Setuprecord.object_list:
            _purefld_rec = None

    _icomp.value = icomp
    
    _rppurefld_(byref(_icomp))

    return _prop(fixicomp = icomp)
            
          
def _name(icomp=1):
    _inputerrorcheck(locals())
    _icomp.value = icomp
    
    _rpname_(byref(_icomp), byref(_hname), byref(_hn80), byref(_hcas),
             c_long(12), c_long(80), c_long(12))
    
    return _hname.value.decode(u'utf-8').strip().upper()  
            

def name(icomp=1):
    u'''Provides name information for specified component

    input:
        icomp--component number in mixture; 1 for pure fluid
    outputs:
        hname--component name [character*12]
        hn80--component name--long form [character*80]
        hcas--CAS (Chemical Abstracts Service) number [character*12]'''
    _inputerrorcheck(locals())
    _icomp.value = icomp

    _rpname_(byref(_icomp), byref(_hname), byref(_hn80), byref(_hcas),
             c_long(12), c_long(80), c_long(12))
    
    return _prop(icomp = icomp,
                        hname = _hname.value.decode(u'utf-8').strip().upper(),
                        hn80 = _hn80.value.decode(u'utf-8').strip().upper(),
                        hcas = _hcas.value.decode(u'utf-8').strip().upper())
                        

def entro(t, D, x):
    u'''Compute entropy as a function of temperature, density and composition
    using core functions (temperature derivative of Helmholtz free energy
    and ideal gas integrals)

    based on derivations in Younglove & McLinden, JPCRD 23 #5, 1994,
    equations A5, A19 - A26

    inputs:
        t--temperature [K]
        D--molar density [mol/L]
        x--composition [array of mol frac]
    output:
        s--entropy [J/mol-K]'''
    _inputerrorcheck(locals())
    _t.value, _D.value = t, D
    for each in xrange(len(x)): _x[each] = x[each]
    
    _rpentro_(byref(_t), byref(_D), _x, byref(_s))
    
    return _prop(x = x, D = D, t = t, s = _s.value)
        

def enthal(t, D, x):
    u'''Compute enthalpy as a function of temperature, density, and
    composition using core functions (Helmholtz free energy and ideal gas
    integrals)

    based on derivations in Younglove & McLinden, JPCRD 23 #5, 1994,
    equations A7, A18, A19

    inputs:
        t--temperature [K]
        D--molar density [mol/L]
        x--composition [array of mol frac]
    output:
        h--enthalpy [J/mol]'''
    _inputerrorcheck(locals())
    _t.value, _D.value = t, D
    for each in xrange(len(x)): _x[each] = x[each]

    _rpenthal_(byref(_t), byref(_D), _x, byref(_h))
    
    return _prop(x = x, D = D, t = t, h = _h.value)


def cvcp(t, D, x):
    u'''Compute isochoric (constant volume) and isobaric (constant pressure)
    heat capacity as functions of temperature, density, and composition
    using core functions

    based on derivations in Younglove & McLinden, JPCRD 23 #5, 1994,
    equation A15, A16

    inputs:
        t--temperature [K]
        D--molar density [mol/L]
        x--composition [array of mol frac]
    outputs:
        cv--isochoric heat capacity [J/mol-K]
        cp--isobaric heat capacity [J/mol-K]'''
    _inputerrorcheck(locals())
    _t.value, _D.value = t, D
    for each in xrange(len(x)): _x[each] = x[each]
    
    _rpcvcp_(byref(_t), byref(_D), _x, byref(_cv), byref(_cp))
    
    return _prop(x = x, D = D, t = t, cv = _cv.value, cp = _cp.value)


def cvcpk(icomp, t, D):
    u'''Compute isochoric (constant volume) and isobaric (constant pressure)
    heat capacity as functions of temperature for a given component.

    analogous to CVCP, except for component icomp, this is used by transport
    routines to calculate Cv & Cp for the reference fluid (component zero)

    inputs:
        icomp--component number in mixture (1..nc); 1 for pure fluid
        t--temperature [K]
        D--molar density [mol/L]
    outputs:
        cv--isochoric heat capacity [J/mol-K]
        cp--isobaric heat capacity [J/mol-K]'''
    _inputerrorcheck(locals())
    _icomp.value, _t.value, _D.value = icomp, t, D
    
    _rpcvcpk_(byref(_icomp), byref(_t), byref(_D), byref(_cv), byref(_cp))
    
    return _prop(icomp = icomp, D = D, t = t, cv = _cv.value, cp = _cp.value)


def gibbs(t, D, x):
    u'''Compute residual Helmholtz and Gibbs free energy as a function of
    temperature, density, and composition using core functions

    N.B.  The quantity calculated is

    G(T, D) - G0(T, P*) = G(T, D) - G0(T, D) + RTln(RTD/P*)
        where G0 is the ideal gas state and P* is a reference pressure which
        is equal to the current pressure of interest. Since Gr is used only
        as a difference in phase equilibria calculations where the
        temperature and pressure of the phases are equal, the (RT/P*) part of
        the log term will cancel and is omitted.

    "normal" (not residual) A and G are computed by subroutine AG

    based on derivations in Younglove & McLinden, JPCRD 23 #5, 1994,
    equations A8 - A12

    inputs:
        t--temperature [K]
        D--molar density [mol/L]
        x--composition [array of mol frac]
    outputs:
        Ar--residual Helmholtz free energy [J/mol]
        Gr--residual Gibbs free energy [J/mol]'''
    _inputerrorcheck(locals())
    _t.value, _D.value = t, D
    for each in xrange(len(x)): _x[each] = x[each]
    
    _rpgibbs_(byref(_t), byref(_D), _x, byref(_Ar), byref(_Gr))

    return _prop(x = x, D = D, t = t, Ar = _Ar.value, Gr = _Gr.value)


def ag(t, D, x):
    u'''Ccompute Helmholtz and Gibbs energies as a function of temperature,
    density, and composition.

    N.B.  These are not residual values (those are calculated by GIBBS).

    inputs:
        t--temperature [K]
        D--molar density [mol/L]
        x--composition [array of mol frac]
    outputs:
        A--Helmholtz energy [J/mol]
        G--Gibbs free energy [J/mol]'''
    _inputerrorcheck(locals())
    _t.value, _D.value = t, D
    for each in xrange(len(x)): _x[each] = x[each]
    
    _rpag_(byref(_t), byref(_D), _x, byref(_A), byref(_G))
    
    return _prop(x = x, D = D, t = t, A = _A.value, G = _G.value)
        

def press(t, D, x):
    u'''Compute pressure as a function of temperature, density, and
    composition using core functions

    direct implementation of core function of corresponding model

    inputs:
        t--temperature [K]
        D--molar density [mol/L]
        x--composition [array of mol frac]
    output:
        p--pressure [kPa]'''
    _inputerrorcheck(locals())
    _t.value, _D.value = t, D
    for each in xrange(len(x)): _x[each] = x[each]
    
    _rppress_(byref(_t), byref(_D), _x, byref(_p))

    return _prop(x = x, D = D, t = t, p = _p.value)


def dpdd(t, D, x):
    u'''Compute partial derivative of pressure w.r.t. density at constant
    temperature as a function of temperature, density, and composition

    inputs:
        t--temperature [K]
        D--molar density [mol/L]
        x--composition [array of mol frac]
    output:
        dpdD--dP/dD [kPa-L/mol]'''
    _inputerrorcheck(locals())
    _t.value, _D.value = t, D
    for each in xrange(len(x)): _x[each] = x[each]
    
    _rpdpdd_(byref(_t), byref(_D), _x, byref(_dpdD))
    
    return _prop(x = x, D = D, t = t, dpdD = _dpdD.value)
        
        
def dpddk(icomp, t, D):
    u'''Compute partial derivative of pressure w.r.t. density at constant
    temperature as a function of temperature and density for a specified
    component

    analogous to dpdd, except for component icomp, this is used by transport
    routines to calculate dP/dD for the reference fluid (component zero)

    inputs:
        icomp--component number in mixture (1..nc); 1 for pure fluid
        t--temperature [K]
        D--molar density [mol/L]
    output:
        dpdD--dP/dD [kPa-L/mol]'''
    _inputerrorcheck(locals())
    _icomp.value, _t.value, _D.value = icomp, t, D
    
    _rpdpddk_(byref(_icomp), byref(_t), byref(_D), byref(_dpdD))
    
    return _prop(icomp = icomp, D = D, t = t, cv = _dpdD.value)
        
        
def dpdd2(t, D, x):
    u'''Compute second partial derivative of pressure w.r.t. density at
    const. temperature as a function of temperature, density, and
    composition.

    inputs:
        t--temperature [K]
        D--molar density [mol/L]
        x--composition [array of mol frac]
    output:
        d2pdD2--d^2P/dD^2 [kPa-L^2/mol^2]'''
    _inputerrorcheck(locals())
    _t.value, _D.value = t, D
    for each in xrange(len(x)): _x[each] = x[each]
    
    _rpdpdd2_(byref(_t), byref(_D), _x, byref(_d2pdD2))
    
    return _prop(x = x, D = D, t = t, d2pdD2 = _d2pdD2.value)


def dpdt(t, D, x):
    u'''Compute partial derivative of pressure w.r.t. temperature at constant
    density as a function of temperature, density, and composition.

    inputs:
        t--temperature [K]
        D--molar density [mol/L]
        x--composition [array of mol frac]
    output:
        dpdt--dp/dt [kPa/K]'''
    _inputerrorcheck(locals())
    _t.value, _D.value = t, D
    for each in xrange(len(x)): _x[each] = x[each]

    _rpdpdt_(byref(_t), byref(_D), _x, byref(_dpdt))
    
    return _prop(x = x, D = D, t = t, dpt = _dpdt.value)
        

def dpdtk(icomp, t, D):
    u'''Compute partial derivative of pressure w.r.t. temperature at constant
    density as a function of temperature and density for a specified
    component

    analogous to dpdt, except for component icomp, this is used by transport
    routines to calculate dP/dT

    inputs:
        icomp--component number in mixture (1..nc); 1 for pure fluid
        t--temperature [K]
        D--molar density [mol/L]
    output:
        dpdt--dP/dT [kPa/K]'''
    _inputerrorcheck(locals())
    _icomp.value, _t.value, _D.value = icomp, t, D

    _rpdpdtk_(byref(_icomp), byref(_t), byref(_D), byref(_dpdt))
    
    return _prop(icomp = icomp, D = D, t = t, dpdt = _dpdt.value)
    
        
def dddp(t, D, x):
    u'''ompute partial derivative of density w.r.t. pressure at constant
    temperature as a function of temperature, density, and composition.

    inputs:
        t--temperature [K]
        D--molar density [mol/L]
        x--composition [array of mol frac]
    output:
        dDdp--dD/dP [mol/(L-kPa)]'''
    _inputerrorcheck(locals())
    _t.value, _D.value = t, D
    for each in xrange(len(x)): _x[each] = x[each]
    
    _rpdddp_(byref(_t), byref(_D), _x, byref(_dDdp))

    return _prop(x = x, D = D, t = t, dDdp = _dDdp.value)
        

def dddt(t, D, x):
    u'''Compute partial derivative of density w.r.t. temperature at constant
    pressure as a function of temperature, density, and composition.

    inputs:
        t--temperature [K]
        D--molar density [mol/L]
        x--composition [array of mol frac]
    output:
        dDdt--dD/dT [mol/(L-K)]; (D)/d(t) = -d(D)/dp x dp/dt = -dp/dt /
        (dp/d(D))'''
    _inputerrorcheck(locals())
    _t.value, _D.value = t, D
    for each in xrange(len(x)): _x[each] = x[each]
    
    _rpdddt_(byref(_t), byref(_D), _x, byref(_dDdt))
    
    return _prop(x = x, D = D, t = t, dDdt = _dDdt.value)
    
        
def dcdt(t, x):
    u'''Compute the 1st derivative of C (C is the third virial coefficient) with
    respect to T as a function of temperature and composition.

    inputs:
        t--temperature [K]
        x--composition [array of mol frac]
    outputs:
        dct--1st derivative of C with respect to T [(L/mol)^2-K]'''
    _inputerrorcheck(locals())
    _t.value = t
    for each in xrange(len(x)): _x[each] = x[each]
    
    _rpdcdt_(byref(_t), _x, byref(_dct))
    
    return _prop(x = x, t = t, dct = _dct.value)
        
        
def dcdt2(t, x):
    u'''Compute the 2nd derivative of C (C is the third virial coefficient) with
    respect to T as a function of temperature and composition.

    inputs:
        t--temperature [K]
        x--composition [array of mol frac]
    outputs:
        dct2--2nd derivative of C with respect to T [(L/mol-K)^2]'''
    _inputerrorcheck(locals())
    _t.value = t
    for each in xrange(len(x)): _x[each] = x[each]
    
    _rpdcdt2_(byref(_t), _x, byref(_dct2))
    
    return _prop(x = x, t = t, dct2 = _dct2.value)
        
        
def dhd1(t, D, x):
    u'''Compute partial derivatives of enthalpy w.r.t. t, p, or D at constant
    t, p, or D as a function of temperature, density, and composition

    inputs:
        t--temperature [K]
        D--molar density [mol/L]
        x--composition [array of mol frac]
    output:
        dhdt_D--dh/dt [J/mol-K]
        dhdt_p--dh/dt [J/mol-K]
        dhdD_t--dh/dD [J-L/mol^2]
        dhdD_p--dh/dD [J-L/mol^2]
        dhdp_t--dh/dt [J/mol-kPa]
        dhdp_D--dh/dt [J/mol-kPA]'''
    _inputerrorcheck(locals())
    _t.value, _D.value = t, D
    for each in xrange(len(x)): _x[each] = x[each]

    _rpdhd1_(byref(_t), byref(_D), _x, byref(_dhdt_D), byref(_dhdt_p),
              byref(_dhdD_t), byref(_dhdD_p), byref(_dhdp_t), byref(_dhdp_D))
    
    return _prop(x = x, D = D, t = t, dhdt_D = _dhdt_D.value,
        dhdt_p = _dhdt_p.value, dhdD_t = _dhdD_t.value, dhdD_p = _dhdD_p.value,
        dhdp_t = _dhdp_t.value, dhdtp_D = _dhdp_D.value)
        
            
def fgcty(t, D, x):
    u'''Compute fugacity for each of the nc components of a mixture by
    numerical differentiation (using central differences) of the
    dimensionless residual Helmholtz energy

    based on derivations in E.W. Lemmon, MS Thesis, University of Idaho
    (1991); section 3.2

    inputs:
        t--temperature [K]
        D--molar density [mol/L]
        x--composition [array of mol frac]
    output:
        f--array (1..nc) of fugacities [kPa]'''
    _inputerrorcheck(locals())
    _t.value, _D.value = t, D
    for each in xrange(len(x)): _x[each] = x[each]

    _rpfgcty_(byref(_t), byref(_D), _x, _f)

    return _prop(x = x, D = D, t = t,
                        f = [_f[each] for each in xrange(_nc_rec.record)])


def fgcty2(t, D, x):
    u'''Compute fugacity for each of the nc components of a mixture by
    analytical differentiation of the dimensionless residual Helmholtz energy.

    based on derivations in the GERG-2004 document for natural gas

    inputs:
        t--temperature [K]
        D--molar density [mol/L]
        x--composition [array of mol frac]
    outputs:
        f--array (1..nc) of fugacities [kPa]

    fgcty2 does not work proper on either Linux and Windows operating platform'''
    raise RefproproutineError(u'function "fgcty2" unsupported in Linux & Windows')
    #fgcty2 returns value of fgcty and next refprop call is being
    #blocked by ctypes
    #~ _inputerrorcheck(locals())
    #~ _t.value, _D.value = t, D
    #~ for each in range(len(x)): _x[each] = x[each]
    #~
    #~ raise RefproproutineError('function "fgcty2" unsupported in Linux')

    #~ return _prop(x = x, D = D, t = t, f = [_f[each] for each in range(_nc_rec.record)])
    

def fugcof(t, D, x):
    u'''Compute the fugacity coefficient for each of the nc components of a
    mixture.

    inputs:
        t--temperature [K]
        D--molar density [mol/L]
        x--composition [array of mol frac]
    outputs:
        f--array (1..nc) of the fugacity coefficients'''
    _inputerrorcheck(locals())

    _t.value, _D.value = t, D
    for each in xrange(len(x)): _x[each] = x[each]

    _rpfugcof_(byref(_t), byref(_D), _x, _f, byref(_ierr), byref(_herr),
               c_long(255))

    return _prop(x = x, D = D, t = t,
                    f = [_f[each] for each in xrange(_nc_rec.record)],
                    ierr = _ierr.value, herr = _herr.value, defname = u'fugcof')
                        
                        
def dbdt(t, x):
    u'''Compute the 2nd derivative of B (B is the second virial coefficient)
    with respect to T as a function of temperature and composition.

    inputs:
        t--temperature [K]
        x--composition [array of mol frac]
    outputs:
        dbt--2nd derivative of B with respect to T [L/mol-K]'''
    _inputerrorcheck(locals())
    _t.value = t
    for each in xrange(len(x)): _x[each] = x[each]

    _rpdbdt_(byref(_t), _x, byref(_dbt))
    
    return _prop(x = x, t = t, dbt = _dbt.value)
    

def virb(t, x):
    u'''Compute second virial coefficient as a function of temperature and
    composition.

    inputs:
        t--temperature [K]
        x--composition [array of mol frac]
    outputs:
        b--second virial coefficient [L/mol]'''
    _inputerrorcheck(locals())
    _t.value = t
    for each in xrange(len(x)): _x[each] = x[each]

    _rpvirb_(byref(_t), _x, byref(_b))

    return _prop(x = x, t = t, b = _b.value)
        

def virc(t, x):
    u'''Compute the third virial coefficient as a function of temperature and
    composition.

    inputs:
        t--temperature [K]
        x--composition [array of mol frac]
    outputs:
        c--third virial coefficient [(L/mol)^2]'''
    _inputerrorcheck(locals())
    _t.value = t
    for each in xrange(len(x)): _x[each] = x[each]

    _rpvirc_(byref(_t), _x, byref(_c))

    return _prop(x = x, t = t, c = _c.value)
    
        
def vird(t, x):
    u'''Compute the fourth virial coefficient as a function of temperature
    and composition.

    Routine not supported in Windows

    inputs:
        t--temperature [K]
        x--composition [array of mol frac]
    outputs:
        c--third virial coefficient [(L/mol)^3]'''
    _inputerrorcheck(locals())
    _t.value = t
    for each in xrange(len(x)): _x[each] = x[each]

    _rpvird_(byref(_t), _x, byref(_d))

    return _prop(x = x, t = t, d = _d.value)
    

def virba (t, x):
    u'''Compute second acoustic virial coefficient as a function of temperature
    and composition.

    inputs:
        t--temperature [K]
        x--composition [array of mol frac]
    outputs:
        ba--second acoustic virial coefficient [L/mol]'''
    _inputerrorcheck(locals())
    _t.value = t
    for each in xrange(len(x)): _x[each] = x[each]
    
    _rpvirba_(byref(_t), _x, byref(_ba))
    
    return _prop(x = x, t = t, ba = _ba.value)


def virca(t, x):
    u'''Compute third acoustic virial coefficient as a function of temperature
    and composition.

    inputs:
        t--temperature [K]
        x--composition [array of mol frac]
    outputs:
        ca--third acoustic virial coefficient [(L/mol)^2]'''
    _inputerrorcheck(locals())
    _t.value = t
    for each in xrange(len(x)): _x[each] = x[each]
    
    _rpvirca_(byref(_t), _x, byref(_ca))
    
    return _prop(x = x, t = t, ca = _ca.value)
    
    
def satt(t, x, kph=2):
    u'''Iterate for saturated liquid and vapor states given temperature and
    the composition of one phase

    inputs:
        t--temperature [K]
        x--composition [array of mol frac] (phase specified by kph)
        kph--phase flag:
            1 = input x is liquid composition (bubble point)
            2 = input x is vapor composition (dew point)
            3 = input x is liquid composition (freezing point)
            4 = input x is vapor composition (sublimation point)
    outputs:
        p--pressure [kPa]
        Dliq--molar density [mol/L] of saturated liquid
        Dvap--molar density [mol/L] of saturated vapor
            For a pseudo pure fluid, the density of the equilibrium phase is
            not returned. Call SATT twice, once with kph=1 to get pliq and
            Dliq, and once with kph=2 to get pvap and Dvap.
        xliq--liquid phase composition [array of mol frac]
        xvap--vapor phase composition [array of mol frac]'''

    _inputerrorcheck(locals())
    _t.value, _kph.value = t, kph
    for each in xrange(len(x)): _x[each] = x[each]

    _rpsatt_(byref(_t), _x, byref(_kph), byref(_p), byref(_Dliq),
             byref(_Dvap), _xliq, _xvap, byref(_ierr), byref(_herr), c_long(255))

    xliq = normalize([_xliq[each] for each in xrange(_nc_rec.record)])[u'x']
    xvap = normalize([_xvap[each] for each in xrange(_nc_rec.record)])[u'x']
    if u'_purefld_rec' in _Setuprecord.object_list \
    and len(x) == 1:
        if len(x) != len(xliq):
            xliq = [xliq[_purefld_rec.record[u'icomp'] - 1]]
        if len(x) != len(xvap):
            xvap = [xvap[_purefld_rec.record[u'icomp'] - 1]]
    if u'_purefld_rec' in _Setuprecord.object_list \
    and len(x) == 1:
        if len(x) != len(xliq):
            xliq = [xliq[_purefld_rec.record[u'icomp'] - 1]]
        if len(x) != len(xvap):
            xvap = [xvap[_purefld_rec.record[u'icomp'] - 1]]
    return _prop(t = t, x = x, kph = kph, p = _p.value, Dliq = _Dliq.value,
            Dvap = _Dvap.value, xliq = xliq, xvap = xvap, ierr = _ierr.value,
            herr = _herr.value, defname = u'satt')


def satp(p, x, kph=2):
    u'''Iterate for saturated liquid and vapor states given pressure and the
    composition of one phase.

    inputs:
        p--pressure [kPa]
        x--composition [array of mol frac] (phase specified by kph)
        kph--phase flag:
            1 = input x is liquid composition (bubble point)
            2 = input x is vapor composition (dew point)
            3 = input x is liquid composition (freezing point)
            4 = input x is vapor composition (sublimation point)
    outputs:
        t--temperature [K]
        Dliq--molar density [mol/L] of saturated liquid
        Dvap--molar density [mol/L] of saturated vapor
            For a pseudo pure fluid, the density of the equilibrium phase is
            not returned. Call SATP twice, once with kph=1 to get tliq and
            Dliq, and once with kph=2 to get tvap and Dvap.
        xliq--liquid phase composition [array of mol frac]
        xvap--vapor phase composition [array of mol frac]'''

    _inputerrorcheck(locals())
    _p.value, _kph.value = p, kph
    for each in xrange(len(x)): _x[each] = x[each]
    
    _rpsatp_(byref(_p), _x, byref(_kph), byref(_t), byref(_Dliq),
              byref(_Dvap), _xliq, _xvap, byref(_ierr), byref(_herr), c_long(255))

    xliq = normalize([_xliq[each] for each in xrange(_nc_rec.record)])[u'x']
    xvap = normalize([_xvap[each] for each in xrange(_nc_rec.record)])[u'x']
    if u'_purefld_rec' in _Setuprecord.object_list \
    and len(x) == 1:
        if len(x) != len(xliq):
            xliq = [xliq[_purefld_rec.record[u'icomp'] - 1]]
        if len(x) != len(xvap):
            xvap = [xvap[_purefld_rec.record[u'icomp'] - 1]]
    return _prop(p = p, x = x, kph = kph, t = _t.value, Dliq = _Dliq.value,
            Dvap = _Dvap.value, xliq = xliq, xvap = xvap, ierr = _ierr.value,
            herr = _herr.value, defname = u'satp')


def satd(D, x, kph=2):
    u'''Iterate for temperature and pressure given a density along the
    saturation boundary and the composition.

    inputs:
        D--molar density [mol/L]
        x--composition [array of mol frac]
        kph--flag specifying desired root for multi-valued inputs
            has meaning only for water at temperatures close to its triple
            point -1 = return middle root (between 0 and 4 C) 1 = return
            highest temperature root (above 4 C) 3 = return lowest temperature
            root (along freezing line)
    outputs:
        t--temperature [K]
        p--pressure [kPa]
        Dliq--molar density [mol/L] of saturated liquid
        Dvap--molar density [mol/L] of saturated vapor
        xliq--liquid phase composition [array of mol frac]
        xvap--vapor phase composition [array of mol frac]
        kr--phase flag:
            1 = input state is liquid
            2 = input state is vapor in equilibrium with liq
            3 = input state is liquid in equilibrium with solid
            4 = input state is vapor in equilibrium with solid
            N.B. kr = 3,4 presently working only for pure components

    either (Dliq, xliq) or (Dvap, xvap) will correspond to the input state
    with the other pair corresponding to the other phase in equilibrium with
    the input state'''

    _inputerrorcheck(locals())
    _D.value, _kph.value = D, kph
    for each in xrange(len(x)):
        _x[each] = x[each]

    _rpsatd_(byref(_D), _x, byref(_kph), byref(_kr), byref(_t), byref(_p),
              byref(_Dliq), byref(_Dvap), _xliq, _xvap, byref(_ierr),
              byref(_herr), c_long(255))

    xliq = normalize([_xliq[each] for each in xrange(_nc_rec.record)])[u'x']
    xvap = normalize([_xvap[each] for each in xrange(_nc_rec.record)])[u'x']
    if u'_purefld_rec' in _Setuprecord.object_list \
    and len(x) == 1:
        if len(x) != len(xliq):
            xliq = [xliq[_purefld_rec.record[u'icomp'] - 1]]
        if len(x) != len(xvap):
            xvap = [xvap[_purefld_rec.record[u'icomp'] - 1]]
    return _prop(D = D, x = x, kph = kph, kr = _kr.value, t = _t.value,
        p = _p.value, Dliq = _Dliq.value, Dvap = _Dvap.value, xliq = xliq,
        xvap = xvap, ierr = _ierr.value, herr = _herr.value, defname = u'satd')


def sath(h, x, kph=2):
    u'''Iterate for temperature, pressure, and density given enthalpy along
    the saturation boundary and the composition.

    inputs:
        h--molar enthalpy [J/mol]
        x--composition [array of mol frac]
        kph--flag specifying desired root:
            0 = return all roots along the liquid-vapor line
            1 = return only liquid VLE root
            2 = return only vapor VLE roots
            3 = return liquid SLE root (melting line)
            4 = return vapor SVE root (sublimation line)
    outputs:
        nroot--number of roots.  Set to one for kph=1,3,4 if ierr=0
        k1--phase of first root (1-liquid, 2-vapor, 3-melt, 4-subl)
        t1--temperature of first root [K]
        p1--pressure of first root [kPa]
        D1--molar density of first root [mol/L]
        k2--phase of second root (1-liquid, 2-vapor, 3-melt, 4-subl)
        t2--temperature of second root [K]
        p2--pressure of second root [kPa]
        D2--molar density of second root [mol/L]

    The second root is always set as the root in the vapor at temperatures
    below the maximum enthalpy on the vapor saturation line. If kph is set
    to 2, and only one root is found in the vapor (this occurs when h <
    hcrit) the state point will be placed in k2,t2,p2,d2. If kph=0 and this
    situation occurred, the first root (k1,t1,p1,d1) would be in the liquid
    (k1=1, k2=2).

    N.B. kph = 3,4 presently working only for pure components'''

    _inputerrorcheck(locals())
    _h.value, _kph.value = h, kph
    for each in xrange(len(x)): _x[each] = x[each]
    
    _rpsath_(byref(_h), _x, byref(_kph), byref(_nroot), byref(_k1),
              byref(_t1), byref(_p1), byref(_D1), byref(_k2), byref(_t2),
              byref(_p2), byref(_D2), byref(_ierr), byref(_herr), c_long(255))
    
    return _prop(h = h, x = x, kph = kph, nroot = _nroot.value, k1 = _k1.value,
            t1 = _t1.value, p1 = _p1.value, D1 = _D1.value, k2 = _k2.value,
            t2 = _t2.value, p2 = _p2.value, D2 = _D2.value, ierr = _ierr.value,
            herr = _herr.value, defname = u'sath')
            

def sate(e, x, kph=2):
    u'''Iterate for temperature, pressure, and density given energy along the
    saturation boundary and the composition.

    inputs:
        e--molar energy [J/mol]
        x--composition [array of mol frac]
        kph--flag specifying desired root:
            0 = return all roots along the liquid-vapor line
            1 = return only liquid VLE root
            2 = return only vapor VLE roots
            3 = return liquid SLE root (melting line)
            4 = return vapor SVE root (sublimation line)
    outputs:
        nroot--number of roots.  Set to one for kph=1,3,4 if ierr=0
        k1--phase of first root (1-liquid, 2-vapor, 3-melt, 4-subl)
        t1--temperature of first root [K]
        p1--pressure of first root [kPa]
        D1--molar density of first root [mol/L]
        k2--phase of second root (1-liquid, 2-vapor, 3-melt, 4-subl)
        t2--temperature of second root [K]
        p2--pressure of second root [kPa]
        D2--molar density of second root [mol/L]

    The second root is always set as the root in the vapor at temperatures
    below the maximum energy on the vapor saturation line. If kph is set to
    2, and only one root is found in the vapor (this occurs when h < hcrit)
    the state point will be placed in k2,t2,p2,d2. If kph=0 and this
    situation occurred, the first root (k1,t1,p1,d1) would be in the liquid
    (k1=1, k2=2).

    N.B. kph = 3,4 presently working only for pure components'''

    _inputerrorcheck(locals())
    _e.value, _kph.value = e, kph
    for each in xrange(len(x)): _x[each] = x[each]
    
    _rpsate_(byref(_e), _x, byref(_kph), byref(_nroot), byref(_k1),
              byref(_t1), byref(_p1), byref(_D1),byref(_k2), byref(_t2),
              byref(_p2), byref(_D2), byref(_ierr), byref(_herr), c_long(255))

    return _prop(e = e, x = x, kph = kph, nroot = _nroot.value, k1 = _k1.value,
            t1 = _t1.value, p1 = _p1.value, D1 = _D1.value, k2 = _k2.value,
            t2 = _t2.value, p2 = _p2.value, D2 = _D2.value, ierr = _ierr.value,
            herr = _herr.value, defname = u'sate')
                
                
def sats(s, x, kph=2):
    u'''Iterate for temperature, pressure, and density given entropy along
    the saturation boundary and the composition.

    inputs:
        s--entrophy [J/(mol K)]
        x--composition [array of mol frac]
        kph--flag specifying desired root:
            0 = return all roots along the liquid-vapor line
            1 = return only liquid VLE root
            2 = return only vapor VLE roots
            3 = return liquid SLE root (melting line)
            4 = return vapor SVE root (sublimation line)
    outputs:
        nroot--number of roots.  Set to one for kph=1,3,4 if ierr=0
        k1--phase of first root (1-liquid, 2-vapor, 3-melt, 4-subl)
        t1--temperature of first root [K]
        p1--pressure of first root [kPa]
        D1--molar density of first root [mol/L]
        k2--phase of second root (1-liquid, 2-vapor, 3-melt, 4-subl)
        t2--temperature of second root [K]
        p2--pressure of second root [kPa]
        D2--molar density of second root [mol/L]
        k3--phase of third root (1-liquid, 2-vapor, 3-melt, 4-subl)
        t3--temperature of third root [K]
        p3--pressure of third root [kPa]
        D3--molar density of third root [mol/L]

    The second root is always set as the root in the vapor at temperatures
    below the maximum energy on the vapor saturation line. If kph is set to
    2, and only one root is found in the vapor (this occurs when h < hcrit)
    the state point will be placed in k2,t2,p2,d2. If kph=0 and this
    situation occurred, the first root (k1,t1,p1,d1) would be in the liquid
    (k1=1, k2=2).

    The third root is the root with the lowest temperature. For fluids with
    multiple roots:  When only one root is found in the vapor phase (this
    happens only at very low temperatures past the region where three roots
    are located), the value of the root is still placed in k3,t3,p3,d3. For
    fluids that never have more than one root (when there is no maximum
    entropy along the saturated vapor line), the value of the root is always
    placed in k1,t1,p1,d1.

    N.B. kph = 3,4 presently working only for pure components'''

    _inputerrorcheck(locals())
    _s.value, _kph.value = s, kph
    for each in xrange(len(x)): _x[each] = x[each]

    _rpsats_(byref(_s), _x, byref(_kph), byref(_nroot), byref(_k1),
              byref(_t1), byref(_p1), byref(_D1), byref(_k2), byref(_t2),
              byref(_p2), byref(_D2), byref(_k3), byref(_t3), byref(_p3),
              byref(_D3), byref(_ierr), byref(_herr), c_long(255))

    return _prop(s = s, x = x, kph = kph, nroot = _nroot.value, k1 = _k1.value,
            t1 = _t1.value, p1 = _p1.value, D1 = _D1.value, k2 = _k2.value,
            t2 = _t2.value, p2 = _p2.value, D2 = _D2.value, k3 = _k3.value,
            t3 = _t3.value, p3 = _p3.value, D3 = _D3.value, ierr = _ierr.value,
            herr = _herr.value, defname = u'sats')
               
               
def csatk(icomp, t, kph=2):
    u'''Compute the heat capacity along the saturation line as a function of
    temperature for a given component

    csat can be calculated two different ways:
        Csat = Cp - t(DvDt)(DpDtsat)
        Csat = Cp - beta/D*hvap/(vliq - vvap),
            where beta is the volume expansivity

    inputs:
        icomp--component number in mixture (1..nc); 1 for pure fluid
        t--temperature [K]
        kph--phase flag:
            1 = liquid calculation
            2 = vapor calculation
    outputs:
        p--saturation pressure [kPa]
        D--saturation molar density [mol/L]
        csat--saturation heat capacity [J/mol-K]'''

    _inputerrorcheck(locals())
    _icomp.value, _t.value, _kph.value = icomp, t, kph

    _rpcsatk_(byref(_icomp), byref(_t), byref(_kph), byref(_p), byref(_D),
               byref(_csat), byref(_ierr), byref(_herr), c_long(255))

    return _prop(icomp = icomp, t = t, kph = kph, p = _p.value, D = _D.value,
            csat = _csat.value, ierr = _ierr.value, herr = _herr.value,
            defname = u'csatk')
            

def dptsatk(icomp, t, kph=2):
    u'''Compute the heat capacity and dP/dT along the saturation line as a
    function of temperature for a given component. See also subroutine
    CSATK.

    inputs:
        icomp--component number in mixture (1..nc); 1 for pure fluid
        t--temperature [K]
        kph--phase flag:
            1 = liquid calculation
            2 = vapor calculation
    outputs:
        p--saturation pressure [kPa]
        D--saturation molar density [mol/L]
        csat--saturation heat capacity [J/mol-K] (same as that called from
            CSATK)
        dpdt--dp/dT along the saturation line [kPa/K]
            (this is not dp/dt "at" the saturation line for the single phase
            state, but the change in saturated vapor pressure as the
            saturation temperature changes.)'''

    _inputerrorcheck(locals())
    _icomp.value, _t.value, _kph.value = icomp, t, kph

    _rpdptsatk_(byref(_icomp), byref(_t), byref(_kph), byref(_p),
                 byref(_D), byref(_csat), byref(_dpdt), byref(_ierr),
                 byref(_herr), c_long(255))

    return _prop(icomp = icomp, t = t, kph = kph, p = _p.value, D = _D.value,
            csat = _csat.value, dpdt = _dpdt.value, ierr = _ierr.value,
            herr = _herr.value, defname = u'dptsatk')
            
            
def cv2pk(icomp, t, D=0):
    u'''Compute the isochoric heat capacity in the two phase (liquid+vapor)
    region.

    inputs:
        icomp--component number in mixture (1..nc); 1 for pure fluid
        t--temperature [K]
        D--density [mol/l] if known
            If D=0, then a saturated liquid state is assumed.
    outputs:
        cv2p--isochoric two-phase heat capacity [J/mol-K]
        csat--saturation heat capacity [J/mol-K]
            (Although there is already a csat routine in REFPROP, it is also
            returned here. However, the calculation speed is slower than
            csat.)'''

    _inputerrorcheck(locals())
    _icomp.value, _t.value, _D.value = icomp, t, D
    
    _rpcv2pk_(byref(_icomp), byref(_t), byref(_D), byref(_cv2p),
               byref(_csat), byref(_ierr), byref(_herr), c_long(255))
    
    return _prop(icomp = icomp, t = t, D = D, cv2p = _cv2p.value,
                    csat = _csat.value, ierr = _ierr.value, herr = _herr.value,
                    defname = u'cv2pk')
                    
                    
def tprho(t, p, x, kph=2, kguess=0, D=0):
    u'''Iterate for density as a function of temperature, pressure, and
    composition for a specified phase.

    The single-phase temperature-pressure flash is called many times by
    other routines, and has been optimized for speed; it requires a specific
    calling sequence.

    ***********************************************************************
    WARNING:
    Invalid densities will be returned for T & P outside range of validity,
    i.e., pressure > melting pressure, pressure less than saturation
    pressure for kph=1, etc.
    ***********************************************************************
    inputs:
        t--temperature [K]
        p--pressure [kPa]
        x--composition [array of mol frac]
        kph--phase flag:
            1 = liquid
            2 = vapor
            0 = stable phase--NOT ALLOWED (use TPFLSH)
                (unless an initial guess is supplied for rho)
            -1 = force the search in the liquid phase
            -2 = force the search in the vapor phase
        kguess--input flag:
            1 = first guess for D provided
            0 = no first guess provided
        D--first guess for molar density [mol/L], only if kguess = 1
    outputs:
        D--molar density [mol/L]'''

    _inputerrorcheck(locals())
    _t.value, _p.value, _kph.value = t, p, kph
    _kguess.value, _D.value = kguess, D
    for each in xrange(len(x)): _x[each] = x[each]

    _rptprho_(byref(_t), byref(_p), _x, byref(_kph), byref(_kguess),
               byref(_D), byref(_ierr), byref(_herr), c_long(255))

    return _prop(t = t, p = p, x = x, kph = kph, kguess = kguess, D = _D.value,
            ierr = _ierr.value, herr = _herr.value, defname = u'tprho')
            
            
def flsh(routine, var1, var2, x, kph=1):
    u'''Flash calculation given two independent variables and bulk
    composition

    These routines accept both single-phase and two-phase states as the
    input; if the phase is known, the specialized routines are faster

    inputs:
        routine--set input variables:
            'TP'--temperature; pressure
            'TD'--temperature; Molar Density
            'TH'--temperature; enthalpy
            'TS'--temperature; entropy
            'TE'--temperature; internal energy
            'PD'--pressure; molar density
            'PH'--pressure; enthalpy
            'PS'--pressure; entropy
            'PE'--pressure; internal energy
            'HS'--enthalpy; entropy
            'ES'--internal energy; entropy
            'DH'--molar density; enthalpy
            'DS'--molar density; entropy
            'DE'--molar density; internal energy
            'TQ'--temperature; vapour quality
            'PQ'--pressure; vapour qaulity
        var1, var2--two of the following as indicated by the routine input:
            t--temperature [K]
            p--pressure [kPa]
            e--internal energy [J/mol]
            h--enthalpy [J/mol]
            s--entropy [[J/mol-K]
            q--vapor quality on molar basis [moles vapor/total moles]
                q = 0 indicates saturated liquid
                0 < q < 1 indicates 2 phase state
                q = 1 indicates saturated vapor
                q < 0 or q > 1 are not allowed and will result in warning
        x--overall (bulk) composition [array of mol frac]
        kph--phase flag:
            N.B. only applicable for routine setting 'TE', 'TH' and 'TS'
            1=liquid,
            2=vapor in equilibrium with liq,
            3=liquid in equilibrium with solid,
            4=vapor in equilibrium with solid.
    outputs:
        t--temperature [K]
        p--pressure [kPa]
        D--overall (bulk) molar density [mol/L]
        Dliq--molar density [mol/L] of the liquid phase
        Dvap--molar density [mol/L] of the vapor phase
            if only one phase is present, Dl = Dv = D
        xliq--composition of liquid phase [array of mol frac]
        xvap--composition of vapor phase [array of mol frac]
            if only one phase is present, x = xliq = xvap
        q--vapor quality on a MOLAR basis [moles vapor/total moles]
            q < 0 indicates subcooled (compressed) liquid
            q = 0 indicates saturated liquid
            0 < q < 1 indicates 2 phase state
            q = 1 indicates saturated vapor
            q > 1 indicates superheated vapor
            q = 998 superheated vapor, but quality not defined (t > Tc)
            q = 999 indicates supercritical state (t > Tc) and (p > Pc)
        e--overall (bulk) internal energy [J/mol]
        h--overall (bulk) enthalpy [J/mol]
        s--overall (bulk) entropy [J/mol-K]
        cv--isochoric (constant V) heat capacity [J/mol-K]
        cp--isobaric (constant p) heat capacity [J/mol-K]
        w--speed of sound [m/s]
            cp, cv and w are not defined for 2-phase states in such cases,
            a flag = -9.99998d6 is returned'''##########################################then remove##################
            #same for kph flag which is only applicable for TH, TE and TS
            #Dvap Dliq to remove if single phase
            #xliq xvap to remove if single phase

    _inputerrorcheck(locals())
    _kph.value = kph
    for each in xrange(len(x)): _x[each] = x[each]
    if routine.upper() == u'TP':
        _t.value, _p.value = var1, var2
        
        _rptpflsh_(byref(_t), byref(_p), _x, byref(_D), byref(_Dliq),
                    byref(_Dvap), _xliq, _xvap, byref(_q), byref(_e), byref(_h),
                    byref(_s), byref(_cv), byref(_cp), byref(_w), byref(_ierr),
                    byref(_herr), c_long(255))

    elif routine.upper() == u'TD':
        _t.value, _D.value = var1, var2

        _rptdflsh_(byref(_t), byref(_D), _x, byref(_p), byref(_Dliq),
                    byref(_Dvap), _xliq, _xvap, byref(_q), byref(_e), byref(_h),
                    byref(_s), byref(_cv), byref(_cp), byref(_w), byref(_ierr),
                    byref(_herr), c_long(255))

    elif routine.upper() == u'TH':
        _t.value, _h.value = var1, var2

        _rpthflsh_(byref(_t), byref(_h), _x, byref(_kph), byref(_p), byref(_D),
                    byref(_Dliq), byref(_Dvap), _xliq, _xvap, byref(_q),
                    byref(_e), byref(_s), byref(_cv), byref(_cp), byref(_w),
                    byref(_ierr), byref(_herr), c_long(255))

    elif routine.upper() == u'TS':
        _t.value, _s.value = var1, var2

        _rptsflsh_(byref(_t), byref(_s), _x, byref(_kph), byref(_p), byref(_D),
                    byref(_Dliq), byref(_Dvap), _xliq, _xvap, byref(_q),
                    byref(_e), byref(_h), byref(_cv), byref(_cp), byref(_w),
                    byref(_ierr), byref(_herr), c_long(255))

    elif routine.upper() == u'TE':
        _t.value, _e.value = var1, var2

        _rpteflsh_(byref(_t), byref(_e), _x, byref(_kph), byref(_p), byref(_D),
                    byref(_Dliq), byref(_Dvap), _xliq, _xvap, byref(_q),
                    byref(_h), byref(_s), byref(_cv), byref(_cp), byref(_w),
                    byref(_ierr), byref(_herr), c_long(255))

    elif routine.upper() == u'PD':
        _p.value, _D.value = var1, var2

        _rppdflsh_(byref(_p), byref(_D), _x, byref(_t), byref(_Dliq),
                    byref(_Dvap), _xliq, _xvap, byref(_q), byref(_e), byref(_h),
                    byref(_s), byref(_cv), byref(_cp), byref(_w), byref(_ierr),
                    byref(_herr), c_long(255))

    elif routine.upper() == u'PH':
        _p.value, _h.value = var1, var2
        
        _rpphflsh_(byref(_p), byref(_h), _x, byref(_t), byref(_D),
                    byref(_Dliq), byref(_Dvap), _xliq, _xvap, byref(_q),
                    byref(_e), byref(_s), byref(_cv), byref(_cp), byref(_w),
                    byref(_ierr), byref(_herr), c_long(255))

    elif routine.upper() == u'PS':
        _p.value, _s.value = var1, var2

        _rppsflsh_(byref(_p), byref(_s), _x, byref(_t), byref(_D),
                    byref(_Dliq), byref(_Dvap), _xliq, _xvap, byref(_q),
                    byref(_e), byref(_h), byref(_cv), byref(_cp), byref(_w),
                    byref(_ierr), byref(_herr), c_long(255))

    elif routine.upper() == u'PE':
        _p.value, _e.value = var1, var2
        
        _rppeflsh_(byref(_p), byref(_e), _x, byref(_t), byref(_D), byref(_Dliq),
                    byref(_Dvap), _xliq, _xvap, byref(_q), byref(_h), byref(_s),
                    byref(_cv), byref(_cp), byref(_w), byref(_ierr),
                    byref(_herr), c_long(255))

    elif routine.upper() == u'HS':
        _h.value, _s.value = var1, var2
        
        _rphsflsh_(byref(_h), byref(_s), _x, byref(_t), byref(_p), byref(_D),
                    byref(_Dliq), byref(_Dvap), _xliq, _xvap, byref(_q), 
                    byref(_e), byref(_cv), byref(_cp), byref(_w), byref(_ierr),
                    byref(_herr), c_long(255))

    elif routine.upper() == u'ES':
        _e.value, _s.value = var1, var2
        
        _rpesflsh_(byref(_e), byref(_s), _x, byref(_t), byref(_p), byref(_D),
                    byref(_Dliq), byref(_Dvap), _xliq, _xvap, byref(_q),
                    byref(_h), byref(_cv), byref(_cp), byref(_w), byref(_ierr),
                    byref(_herr), c_long(255))

    elif routine.upper() == u'DH':
        _D.value, _h.value = var1, var2
        
        _rpdhflsh_(byref(_D), byref(_h), _x, byref(_t), byref(_p), byref(_Dliq),
                    byref(_Dvap), _xliq, _xvap, byref(_q), byref(_e), byref(_s),
                    byref(_cv), byref(_cp), byref(_w), byref(_ierr),
                    byref(_herr), c_long(255))

    elif routine.upper() == u'DS':
        _D.value, _s.value = var1, var2

        _rpdsflsh_(byref(_D), byref(_s), _x, byref(_t), byref(_p), byref(_Dliq),
                    byref(_Dvap), _xliq, _xvap, byref(_q), byref(_e), byref(_h),
                    byref(_cv), byref(_cp), byref(_w), byref(_ierr),
                    byref(_herr), c_long(255))

    elif routine.upper() == u'DE':
        _D.value, _e.value = var1, var2

        _rpdeflsh_(byref(_D), byref(_e), _x, byref(_t), byref(_p), byref(_Dliq),
                    byref(_Dvap), _xliq, _xvap, byref(_q), byref(_h), byref(_s),
                    byref(_cv), byref(_cp), byref(_w), byref(_ierr),
                    byref(_herr), c_long(255))

    elif routine.upper() == u'TQ':
        _t.value, _q.value = var1, var2

        _rptqflsh_(byref(_t), byref(_q), _x, byref(c_long(1)), byref(_p),
                    byref(_D), byref(_Dliq), byref(_Dvap), _xliq, _xvap,
                    byref(_e), byref(_h), byref(_s), byref(_cv), byref(_cp),
                    byref(_w), byref(_ierr), byref(_herr), c_long(255))
    
    elif routine.upper() == u'PQ':
        _p.value, _q.value = var1, var2

        _rppqflsh_(byref(_p), byref(_q), _x, byref(c_long(1)), byref(_t),
                    byref(_D), byref(_Dliq), byref(_Dvap), _xliq, _xvap,
                    byref(_e), byref(_h), byref(_s), byref(_cv), byref(_cp),
                    byref(_w), byref(_ierr), byref(_herr), c_long(255))

    else: raise RefpropinputError(u'Incorrect "routine" input, ' + unicode(routine) +
                                            u' is an invalid input')

    xliq = normalize([_xliq[each] for each in xrange(_nc_rec.record)])[u'x']
    xvap = normalize([_xvap[each] for each in xrange(_nc_rec.record)])[u'x']
    if u'_purefld_rec' in _Setuprecord.object_list \
    and len(x) == 1:
        if len(x) != len(xliq):
            xliq = [xliq[_purefld_rec.record[u'icomp'] - 1]]
        if len(x) != len(xvap):
            xvap = [xvap[_purefld_rec.record[u'icomp'] - 1]]
    return _prop(x = x, p = _p.value, q = _q.value, kph = kph, t = _t.value,
            D = _D.value, Dliq = _Dliq.value, Dvap = _Dvap.value, xliq = xliq,
            xvap = xvap, e = _e.value, h = _h.value, s = _s.value, cv = _cv.value,
            cp = _cp.value, w = _w.value, ierr = _ierr.value, herr = _herr.value,
            defname = u'flsh')
            
            
def flsh1(routine, var1, var2, x, kph=1, Dmin=0, Dmax=0):
    u'''Flash calculation given two independent variables and bulk
    composition

    These routines accept only single-phase states and outside critical
    region as inputs. They will be faster than the corresponding general
    routines, but will fail if called with an incorrect phase specification.
    The phase-specific subroutines also do not check limits, so may fail if
    called outside the range of the equation of state.

    inputs:
        routine--set input variables:
            'TH'--temperature; enthalpy*
            'TS'--temperature; entropy*
            'TE'--temperature; energy*
            'PD'--pressure; molar density
            'PH'--pressure; entalphy
            'PS'--pressure; entropy
            'PE'--pressure; internal energy*
            'HS'--enthalpy; entropy*
            'DH'--molar density; enthalpy*
            'DS'--molar density; entropy*
            'DE'--molar density; internal energy*
            * routine not supported in Windows
        var1, var2--two of the following as indicated by the routine input:
            t--temperature [K]
            p--pressure [kPa]
            e--internal energy [J/mol]
            h--enthalpy [J/mol]
            s--entropy [[J/mol-K]
        x--overall (bulk) composition [array of mol frac]
        kph--phase flag:
            N.B. only applicable for routine setting 'TE', 'TH' and 'TS'
            1 = liquid,
            2 = vapor
        Dmin--lower bound on density [mol/L]
        Dmax--upper bound on density [mol/L]
    outputs:
        t--temperature [K]
        D--overall (bulk) molar density [mol/L]'''
    defname = u'flsh1'

    _inputerrorcheck(locals())
    _kph.value, _Dmin.value, _Dmax.value = kph, Dmin, Dmax
    for each in xrange(len(x)): _x[each] = x[each]
    if routine.upper() == u'TH':
        _t.value, _h.value = var1, var2
        
        _rpthfl1_(byref(_t), byref(_h), _x, byref(_Dmin), byref(_Dmax),
                   byref(_D), byref(_ierr), byref(_herr), c_long(255))

    elif routine.upper() == u'TS':
        _t.value, _s.value = var1, var2

        _rptsfl1_(byref(_t), byref(_s), _x, byref(_Dmin), byref(_Dmax),
                   byref(_D), byref(_ierr), byref(_herr), c_long(255))

    elif routine.upper() == u'TE':
        _t.value, _e.value = var1, var2
        
        _rptefl1_(byref(_t), byref(_e), _x, byref(_Dmin), byref(_Dmax),
                   byref(_D), byref(_ierr), byref(_herr), c_long(255))

    elif routine.upper() == u'PD':
        _p.value, _D.value = var1, var2
        
        _rppdfl1_(byref(_p), byref(_D), _x, byref(_t), byref(_ierr),
                   byref(_herr), c_long(255))

    elif routine.upper() == u'PH':
        _p.value, _h.value = var1, var2
        
        _rpphfl1_(byref(_p), byref(_h), _x, byref(_kph), byref(_t), byref(_D),
                   byref(_ierr), byref(_herr), c_long(255))

    elif routine.upper() == u'PS':
        _p.value, _s.value = var1, var2
        
        _rppsfl1_(byref(_p), byref(_s), _x, byref(_kph),  byref(_t), byref(_D),
                   byref(_ierr), byref(_herr), c_long(255))

    elif routine.upper() == u'PE': #wrong value return
        _p.value, _e.value = var1, var2
        
        _rppefl1_(byref(_p), byref(_e), _x, byref(_kph), byref(_t), byref(_D),
                   byref(_ierr), byref(_herr), c_long(255))

    elif routine.upper() == u'HS':
        _h.value, _s.value = var1, var2

        _rphsfl1_(byref(_h), byref(_s), _x, byref(_Dmin), byref(_Dmax),
                   byref(_t), byref(_D), byref(_ierr), byref(_herr), c_long(255))

    elif routine.upper() == u'DH':
        _D.value, _h.value = var1, var2
        
        _rpdhfl1_(byref(_D), byref(_h), _x, byref(_t), byref(_ierr),
                   byref(_herr), c_long(255))

    elif routine.upper() == u'DS':
        _D.value, _s.value = var1, var2

        _rpdsfl1_(byref(_D), byref(_s), _x, byref(_t), byref(_ierr),
                   byref(_herr), c_long(255))

    elif routine.upper() == u'DE':
        _D.value, _e.value = var1, var2
        
        _rpdefl1_(byref(_D), byref(_e), _x, byref(_t), byref(_ierr),
                   byref(_herr), c_long(255))

    else: raise RefpropinputError(u'Incorrect "routine" input, ' + unicode(routine) +
                                            u' is an invalid input')
    if routine.upper() == u'TH':
        return _prop(x = x, t = var1, Dmin = _Dmin.value, Dmax = _Dmax.value,
                D = _D.value, h = var2, ierr = _ierr.value, herr = _herr.value,
                defname = defname)
    elif routine.upper() == u'TS':
        return _prop(x = x, t = var1, D = _D.value, s = var2, Dmin = _Dmin.value,
                Dmax = _Dmax.value, ierr = _ierr.value, herr = _herr.value,
                defname = defname)
    elif routine.upper() == u'TE':
        return _prop(x = x, t = var1, D = _D.value, e = var2, Dmin = _Dmin.value,
                Dmax = _Dmax.value, ierr = _ierr.value, herr = _herr.value,
                defname = defname)
    elif routine.upper() == u'PD':
        return _prop(x = x, t = _t.value, D = var2, kph = kph, p = var1,
                ierr = _ierr.value, herr = _herr.value, defname = defname)
    elif routine.upper() == u'PH':
        return _prop(x = x, t = _t.value, D = _D.value, kph = kph, p = var1,
                            h = var2, ierr = _ierr.value, herr = _herr.value,
                            defname = defname)
    elif routine.upper() == u'PS':
        return _prop(x = x, t = _t.value, D = _D.value, kph = kph, p = var1,
                        s = var2, ierr = _ierr.value, herr = _herr.value,
                        defname = defname)
    elif routine.upper() == u'PE':
        return _prop(x = x, t = _t.value, D = _D.value, kph = kph, p = var1,
                        e = var2, ierr = _ierr.value, herr = _herr.value,
                        defname = defname)
    elif routine.upper() == u'HS':
        return _prop(x = x, t = _t.value, D = _D.value, h = var1, s = var2,
                ierr = _ierr.value, herr = _herr.value, Dmin = _Dmin.value,
                Dmax = _Dmax.value, defname = defname)
    elif routine.upper() == u'DH':
        return _prop(x = x, t = _t.value, D = var1, h = var2, ierr = _ierr.value,
                herr = _herr.value, defname = defname)
    elif routine.upper() == u'DS':
        return _prop(x = x, t = _t.value, D = var1, s = var2, ierr = _ierr.value,
                herr = _herr.value, defname = defname)
    elif routine.upper() == u'DE':
        return _prop(x = x, t = _t.value, D = var1, e = var2, ierr = _ierr.value,
                herr = _herr.value, defname = defname)
                
def flsh2(routine, var1, var2, x, kq=1, ksat=0, tbub=0, tdew=0, pbub=0, pdew=0,
            Dlbub=0, Dvdew=0, xbub=None, xdew=None):
    u'''Flash calculation given two independent variables and bulk composition

    These routines accept only two-phase (liquid + vapor) states as inputs.
    They will be faster than the corresponding general routines, but will fail if
    called with an incorrect phase specification.
    The phase-specific subroutines also do not check limits, so may fail if
    called outside the range of the equation of state.

    Some two-phase flash routines have the option to pass the dew and bubble
    point conditions as inputs if these values are known
    (from a previous call to SATT or SATP, for example), these two-phase routines
    will be significantly faster than the corresponding
    general FLSH routines described above. Otherwise, the general routines will
    be more reliable.

    inputs:
        routine--set input variables:
            'TP'--temperature; pressure*
            'DH'--molar density; enthalpy*
            'DS'--molar density; entropy*
            'DE'--molar density; internal energy*
            'TH'--temperature; enthalpy*
            'TS'--temperature; entropy*
            'TE'--temperature; internal energy*
            'TD'--temperature; Molar Density*
            'PD'--pressure; molar density*
            'PH'--pressure; entalphy*
            'PS'--pressure; entropy*
            'PE'--pressure; internal energy*
            'TQ'--temperature; vapour quality*
            'PQ'--pressure; vapour qaulity*
            'DQ'--molar density; vapour quality*/**
            * NOT supported with Windows
            ** return value is incorrect
        var1, var2--two of the following as indicated by the routine input:
            t--temperature [K]
            p--pressure [kPa]
            D--molar density [mol/L]
            e--internal energy [J/mol]
            h--enthalpy [J/mol]
            s--entropy [[J/mol-K]
            q--vapor quality on molar basis [moles vapor/total moles]
        x--overall (bulk) composition [array of mol frac]
        kq--flag specifying units for input quality
            NB only for routine (TQ and PQ)
            kq = 1 quality on MOLAR basis [moles vapor/total moles]
            kq = 2 quality on MASS basis [mass vapor/total mass]
        ksat--flag for bubble and dew point limits
            NB only for routine (TH, TS, TE, TD, PD, PH, PS, PE, TQ and PQ)
            0 = dew and bubble point limits computed within routine
            1 = must provide values for following:
                tbub--bubble point temperature [K] at (p,x=z)
                    NB only for routine (PD, PH, PS, PE and PQ)
                tdew--dew point temperature [K] at (p,y=z)
                    NB only for routine (PD, PH, PS, PE and PQ)
                pbub--bubble point pressure [kPa] at (t,x=z)
                    NB only for routine (TH, TS, TE, TD and TQ)
                pdew--dew point pressure [kPa] at (t,y=z)
                    NB only for routine (TH, TS, TE, TD and TQ)
                Dlbub--liquid density [mol/L] at bubble point
                    NB only for routine (TH, TS, TE, TD, PD, PH, PS, PE, TQ and PQ)
                Dvdew--vapor density [mol/L] at dew point
                    NB only for routine (TH, TS, TE, TD, PD, PH, PS, PE, TQ and PQ)
                xbub--vapor composition [array of mol frac] at bubble point
                    NB only for routine (TH, TS, TE, TD, PD, PH, PS, PE, TQ and PQ)
                xdew--liquid composition [array of mol frac] at dew point
                    NB only for routine (TH, TS, TE, TD, PD, PH, PS, PE, TQ and PQ)
    outputs:
        t--temperature [K]
        p--pressure [kPa]
        Dliq--molar density [mol/L] of the liquid phase
        Dvap--molar density [mol/L] of the vapor phase
            if only one phase is present, Dl = Dv = D
        xliq--composition of liquid phase [array of mol frac]
        xvap--composition of vapor phase [array of mol frac]
            if only one phase is present, x = xliq = xvap
        q--vapor quality on a MOLAR basis [moles vapor/total moles]
        tbub--bubble point temperature [K] at (p,x=z)
            NB only for routine (PD, PH, PS, PE and PQ)
        tdew--dew point temperature [K] at (p,y=z)
            NB only for routine (PD, PH, PS, PE and PQ)
        pbub--bubble point pressure [kPa] at (t,x=z)
            NB only for routine (TH, TS, TE, TD and TQ)
        pdew--dew point pressure [kPa] at (t,y=z)
            NB only for routine (TH, TS, TE, TD and TQ)
        Dlbub--liquid density [mol/L] at bubble point
            NB only for routine (TH, TS, TE, TD, PD, PH, PS, PE, TQ and PQ)
        Dvdew--vapor density [mol/L] at dew point
            NB only for routine (TH, TS, TE, TD, PD, PH, PS, PE, TQ and PQ)
        xbub--vapor composition [array of mol frac] at bubble point
            NB only for routine (TH, TS, TE, TD, PD, PH, PS, PE, TQ and PQ)
        xdew--liquid composition [array of mol frac] at dew point
            NB only for routine (TH, TS, TE, TD, PD, PH, PS, PE, TQ and PQ)'''
    defname = u'flsh2'

    _inputerrorcheck(locals())
    for each in xrange(len(x)):
        _x[each] = x[each]
        if xdew: _xdew[each] = xdew[each]
        if xbub: _xbub[each] = xbub[each]
    _ksat.value, _tbub.value, _kq.value = ksat, tbub, kq
    _tdew.value, _pbub.value, _pdew.value = tdew, pbub, pdew
    _Dlbub.value, _Dvdew.value = Dlbub, Dvdew
    if routine.upper() == u'TP':
        _t.value, _p.value = var1, var2
        
        _rptpfl2_(byref(_t), byref(_p), _x, byref(_Dliq), byref(_Dvap), _xliq,
                   _xvap, byref(_q), byref(_ierr), byref(_herr), c_long(255))

    elif routine.upper() == u'DH':
        _D.value, _h.value = var1, var2

        _rpdhfl2_(byref(_D), byref(_h), _x, byref(_t), byref(_p), byref(_Dliq),
                   byref(_Dvap), _xliq, _xvap, byref(_q), byref(_ierr),
                   byref(_herr), c_long(255))

    elif routine.upper() == u'DS':
        _D.value, _s.value = var1, var2

        _rpdsfl2_(byref(_D), byref(_s), _x, byref(_t), byref(_p), byref(_Dliq),
                   byref(_Dvap), _xliq, _xvap, byref(_q), byref(_ierr),
                   byref(_herr), c_long(255))

    elif routine.upper() == u'DE':
        _D.value, _e.value = var1, var2
        
        _rpdefl2_(byref(_D), byref(_e), _x, byref(_t), byref(_p), byref(_Dliq),
                   byref(_Dvap), _xliq, _xvap, byref(_q), byref(_ierr),
                   byref(_herr), c_long(255))

    elif routine.upper() == u'TH':
        _t.value, _h.value = var1, var2
        
        _rpthfl2_(byref(_t), byref(_h), _x, byref(_ksat), byref(_pbub),
                   byref(_pdew), byref(_Dlbub), byref(_Dvdew), _xbub, _xdew,
                   byref(_p), byref(_Dliq), byref(_Dvap), _xliq, _xvap,
                   byref(_q), byref(_ierr), byref(_herr), c_long(255))

    elif routine.upper() == u'TS':
        _t.value, _s.value = var1, var2
        
        _rptsfl2_(byref(_t), byref(_s), _x, byref(_ksat), byref(_pbub),
                   byref(_pdew), byref(_Dlbub), byref(_Dvdew), _xbub, _xdew,
                   byref(_p), byref(_Dliq), byref(_Dvap), _xliq, _xvap,
                   byref(_q), byref(_ierr), byref(_herr), c_long(255))

    elif routine.upper() == u'TE':
        _t.value, _e.value = var1, var2
        
        _rptefl2_(byref(_t), byref(_e), _x, byref(_ksat), byref(_pbub),
                   byref(_pdew), byref(_Dlbub), byref(_Dvdew), _xbub, _xdew,
                   byref(_p), byref(_Dliq), byref(_Dvap), _xliq, _xvap,
                   byref(_q), byref(_ierr), byref(_herr), c_long(255))

    elif routine.upper() == u'TD':
        _t.value, _D.value = var1, var2
        
        _rptdfl2_(byref(_t), byref(_D), _x, byref(_ksat), byref(_pbub),
                   byref(_pdew), byref(_Dlbub), byref(_Dvdew), _xbub, _xdew,
                   byref(_p), byref(_Dliq), byref(_Dvap), _xliq, _xvap,
                   byref(_q), byref(_ierr), byref(_herr), c_long(255))

    elif routine.upper() == u'PD':
        _p.value, _D.value = var1, var2

        _rppdfl2_(byref(_p), byref(_D), _x, byref(_ksat), byref(_tbub),
                   byref(_tdew), byref(_Dlbub), byref(_Dvdew), _xbub, _xdew,
                   byref(_t), byref(_Dliq), byref(_Dvap), _xliq, _xvap,
                   byref(_q), byref(_ierr), byref(_herr), c_long(255))

    elif routine.upper() == u'PH':
        _p.value, _h.value = var1, var2
        
        _rpphfl2_(byref(_p), byref(_h), _x, byref(_ksat), byref(_tbub),
                   byref(_tdew), byref(_Dlbub), byref(_Dvdew), _xbub, _xdew,
                   byref(_t), byref(_Dliq), byref(_Dvap), _xliq, _xvap,
                   byref(_q), byref(_ierr), byref(_herr), c_long(255))

    elif routine.upper() == u'PS':
        _p.value, _s.value = var1, var2
        
        _rppsfl2_(byref(_p), byref(_s), _x, byref(_ksat), byref(_tbub),
                   byref(_tdew), byref(_Dlbub), byref(_Dvdew), _xbub, _xdew,
                   byref(_t), byref(_Dliq), byref(_Dvap), _xliq, _xvap,
                   byref(_q), byref(_ierr), byref(_herr), c_long(255))

    elif routine.upper() == u'PE':
        _p.value, _e.value = var1, var2
        
        _rppefl2_(byref(_p), byref(_e), _x, byref(_ksat), byref(_tbub),
                   byref(_tdew), byref(_Dlbub), byref(_Dvdew), _xbub, _xdew,
                   byref(_t), byref(_Dliq), byref(_Dvap), _xliq, _xvap,
                   byref(_q), byref(_ierr), byref(_herr), c_long(255))

    elif routine.upper() == u'TQ':
        _t.value, _q.value = var1, var2
        
        _rptqfl2_(byref(_t), byref(_q), _x, byref(_kq), byref(_ksat),
                   byref(_pbub), byref(_pdew), byref(_Dlbub), byref(_Dvdew),
                   _xbub, _xdew, byref(_p), byref(_Dliq), byref(_Dvap), _xliq,
                   _xvap, byref(_ierr), byref(_herr), c_long(255))

    elif routine.upper() == u'PQ':
        _p.value, _q.value = var1, var2
        
        _rppqfl2_(byref(_p), byref(_q), _x, byref(_kq), byref(_ksat),
                   byref(_tbub), byref(_tdew), byref(_Dlbub), byref(_Dvdew),
                   _xbub, _xdew, byref(_t), byref(_Dliq), byref(_Dvap), _xliq,
                   _xvap, byref(_ierr), byref(_herr), c_long(255))

    elif routine.upper() == u'DQ':
        _D.value, _q.value = var1, var2

        raise RefproproutineError(u'function "DQFL2" unsupported in Linux')
        ##~ _rpdqfl2_(byref(_D), byref(_q), _x, byref(_kq), byref(_t),
                        #~ byref(_p), byref(_Dliq), byref(_Dvap), _xliq, _xvap,
                        #~ byref(_ierr), byref(_herr), 255)

    else: raise RefpropinputError(u'Incorrect "routine" input, ' +
                                    unicode(routine) +
                                    u' is an invalid input')
    xliq = normalize([_xliq[each] for each in xrange(_nc_rec.record)])[u'x']
    xvap = normalize([_xvap[each] for each in xrange(_nc_rec.record)])[u'x']
    if u'_purefld_rec' in _Setuprecord.object_list \
    and len(x) == 1:
        if len(x) != len(xliq):
            xliq = [xliq[_purefld_rec.record[u'icomp'] - 1]]
        if len(x) != len(xvap):
            xvap = [xvap[_purefld_rec.record[u'icomp'] - 1]]
    if routine.upper() in [u'TH', u'TS', u'TE', u'TD', u'PD', u'PH', u'PS', u'PE',
                           u'TQ', u'PQ', u'DQ']:
        xdew = normalize([_xdew[each] for each in xrange(_nc_rec.record)])[u'x']
        xbub = normalize([_xbub[each] for each in xrange(_nc_rec.record)])[u'x']
        if u'_purefld_rec' in _Setuprecord.object_list \
        and len(x) == 1:
            if len(x) != len(xdew):
                xdew = [xdew[_purefld_rec.record[u'icomp'] - 1]]
            if len(x) != len(xbub):
                xbub = [xbub[_purefld_rec.record[u'icomp'] - 1]]
    if routine.upper() == u'TP':
        return _prop(x = x, t = var1, p = var2, Dliq = _Dliq.value,
                      Dvap = _Dvap.value, xliq = xliq, xvap = xvap,
                      q = _q.value, ierr = _ierr.value, herr = _herr.value,
                      defname = defname)
    elif routine.upper() == u'DH':
        return _prop(x = x, D = var1, h = var2, Dliq = _Dliq.value,
                      Dvap = _Dvap.value, xliq = xliq, xvap = xvap,
                      q = _q.value,t = _t.value, p = _p.value,
                      ierr = _ierr.value, herr = _herr.value, defname = defname)
    elif routine.upper() == u'DS':
        return _prop(x = x, D = var1, s = var2, Dliq = _Dliq.value,
                      Dvap = _Dvap.value, xliq = xliq, xvap = xvap,
                      q = _q.value, t = _t.value, p = _p.value,
                      ierr = _ierr.value, herr = _herr.value, defname = defname)
    elif routine.upper() == u'DE':
        return _prop(x = x, D = var1, e = var2, Dliq = _Dliq.value,
                      Dvap = _Dvap.value, xliq = xliq, xvap = xvap,
                      q = _q.value, t = _t.value, p = _p.value,
                      ierr = _ierr.value, herr = _herr.value, defname = defname)
    elif routine.upper() == u'TH':
        if ksat == 0:
            return _prop(x = x, t = var1, h = var2, Dliq = _Dliq.value,
                          ksat = ksat, Dvap = _Dvap.value, xliq = xliq,
                          xvap = xvap, q = _q.value, p = _p.value,
                          ierr = _ierr.value, herr = _herr.value,
                          pbub = _pbub.value, pdew = _pdew.value,
                          Dlbub = _Dlbub.value, Dvdew = _Dvdew.value,
                          xbub = xbub, xdew = xdew, defname = defname)
        elif ksat == 1:
            return _prop(x = x, t = var1, h = var2, Dliq = _Dliq.value,
                          ksat = ksat, Dvap = _Dvap.value, xliq = xliq,
                          xvap = xvap, q = _q.value, p = _p.value,
                          pbub = _pbub.value, pdew = _pdew.value,
                          Dlbub = _Dlbub.value, Dvdew = _Dvdew.value,
                          xbub = xbub, xdew = xdew, ierr = _ierr.value,
                          herr = _herr.value, defname = defname)
    elif routine.upper() == u'TS':
        if ksat == 0:
            return _prop(x = x, t = var1, s = var2, Dliq = _Dliq.value,
                          Dvap = _Dvap.value, xliq = xliq, xvap = xvap,
                          q = _q.value, p = _p.value, ierr = _ierr.value,
                          herr = _herr.value, pbub = _pbub.value,
                          pdew = _pdew.value, Dlbub = _Dlbub.value,
                          Dvdew = _Dvdew.value, xbub = xbub, xdew = xdew,
                          ksat = ksat, defname = defname)
        elif ksat == 1:
            return _prop(x = x, t = var1, s = var2, Dliq = _Dliq.value,
                          Dvap = _Dvap.value, xliq = xliq, xvap = xvap,
                          q = _q.value, p = _p.value, pbub = _pbub.value,
                          pdew = _pdew.value, Dlbub = _Dlbub.value,
                          Dvdew = _Dvdew.value, xbub = xbub, xdew = xdew,
                          ierr = _ierr.value, herr = _herr.value, ksat = ksat,
                          defname = defname)
    elif routine.upper() == u'TE':
        if ksat == 0:
            return _prop(x = x, t = var1, e = var2, Dliq = _Dliq.value,
                          Dvap = _Dvap.value, xliq = xliq, xvap = xvap,
                          q = _q.value, p = _p.value, ierr = _ierr.value,
                          herr = _herr.value, pbub = _pbub.value,
                          pdew = _pdew.value, Dlbub = _Dlbub.value,
                          Dvdew = _Dvdew.value, xbub = xbub, xdew = xdew,
                          ksat = ksat, defname = defname)
        elif ksat == 1:
            return _prop(x = x, t = var1, e = var2, Dliq = _Dliq.value,
                          Dvap = _Dvap.value, xliq = xliq, xvap = xvap,
                          q = _q.value, p = _p.value, pbub = _pbub.value,
                          pdew = _pdew.value, Dlbub = _Dlbub.value,
                          Dvdew = _Dvdew.value, xbub = xbub, xdew = xdew,
                          ierr = _ierr.value, herr = _herr.value, ksat = ksat,
                          defname = defname)
    elif routine.upper() == u'TD':
        if ksat == 0:
            return _prop(x = x, t = var1, D = var2, Dliq = _Dliq.value,
                          Dvap = _Dvap.value, xliq = xliq, xvap = xvap,
                          q = _q.value, p = _p.value, ierr = _ierr.value,
                          herr = _herr.value, pbub = _pbub.value,
                          pdew = _pdew.value, Dlbub = _Dlbub.value,
                          Dvdew = _Dvdew.value, xbub = xbub, xdew = xdew,
                          ksat = ksat, defname = defname)
        elif ksat == 1:
            return _prop(x = x, t = var1, D = var2, Dliq = _Dliq.value,
                          Dvap = _Dvap.value, xliq = xliq, xvap = xvap,
                          q = _q.value, p = _p.value, pbub = _pbub.value,
                          pdew = _pdew.value, Dlbub = _Dlbub.value,
                          Dvdew = _Dvdew.value, xbub = xbub, xdew = xdew,
                          ierr = _ierr.value, herr = _herr.value, ksat = ksat,
                          defname = defname)
    elif routine.upper() == u'PD':
        if ksat == 0:
            return _prop(x = x, p = var1, D = var2, Dliq = _Dliq.value,
                          Dvap = _Dvap.value, xliq = xliq, xvap = xvap,
                          q = _q.value, t = _t.value, ierr = _ierr.value,
                          herr = _herr.value, tbub = _tbub.value,
                          tdew = _tdew.value, Dlbub = _Dlbub.value,
                          Dvdew = _Dvdew.value, xbub = xbub, xdew = xdew,
                          ksat = ksat, defname = defname)
            return prop
        elif ksat == 1:
            return _prop(x = x, p = var1, D = var2, Dliq = _Dliq.value,
                          Dvap = _Dvap.value, xliq = xliq,    xvap = xvap,
                          q = _q.value, t = _t.value, tbub = _tbub.value,
                          tdew = _tdew.value, Dlbub = _Dlbub.value,
                          Dvdew = _Dvdew.value, xbub = xbub, xdew = xdew,
                          ierr = _ierr.value, herr = _herr.value, ksat = ksat,
                          defname = defname)
    elif routine.upper() == u'PH':
        if ksat == 0:
            return _prop(x = x, p = var1, h = var2, Dliq = _Dliq.value,
                          Dvap = _Dvap.value, xliq = xliq, xvap = xvap,
                          q = _q.value, t = _t.value, ierr = _ierr.value,
                          herr = _herr.value, tbub = _tbub.value,
                          tdew = _tdew.value, Dlbub = _Dlbub.value,
                          Dvdew = _Dvdew.value, xbub = xbub, xdew = xdew,
                          ksat = ksat, defname = defname)
        elif ksat == 1:
            return _prop(x = x, p = var1, h = var2, Dliq = _Dliq.value,
                          Dvap = _Dvap.value, xliq = xliq, xvap = xvap,
                          q = _q.value, t = _t.value, tbub = _tbub.value,
                          tdew = _tdew.value, Dlbub = _Dlbub.value,
                          Dvdew = _Dvdew.value, xbub = xbub, xdew = xdew,
                          ierr = _ierr.value, herr = _herr.value, ksat = ksat,
                          defname = defname)
    elif routine.upper() == u'PS':
        if ksat == 0:
            return _prop(x = x, p = var1, s = var2, Dliq = _Dliq.value,
                          Dvap = _Dvap.value, xliq = xliq, xvap = xvap,
                          q = _q.value, t = _t.value, ierr = _ierr.value,
                          herr = _herr.value, tbub = _tbub.value,
                          tdew = _tdew.value, Dlbub = _Dlbub.value,
                          Dvdew = _Dvdew.value, xbub = xbub, xdew = xdew,
                          ksat = ksat, defname = defname)
        elif ksat == 1:
            return _prop(x = x, p = var1, s = var2, Dliq = _Dliq.value,
                          Dvap = _Dvap.value, xliq = xliq, xvap = xvap,
                          q = _q.value, t = _t.value, tbub = _tbub.value,
                          tdew = _tdew.value, Dlbub = _Dlbub.value,
                          Dvdew = _Dvdew.value, xbub = xbub, xdew = xdew,
                          ierr = _ierr.value, herr = _herr.value, ksat = ksat,
                          defname = defname)
    elif routine.upper() == u'PE':
        if ksat == 0:
            return _prop(x = x, p = var1, e = var2, Dliq = _Dliq.value,
                          Dvap = _Dvap.value, xliq = xliq, xvap = xvap,
                          q = _q.value, t = _t.value, ierr = _ierr.value,
                          herr = _herr.value, tbub = _tbub.value,
                          tdew = _tdew.value, Dlbub = _Dlbub.value,
                          Dvdew = _Dvdew.value, xbub = xbub, xdew = xdew,
                          ksat = ksat, defname = defname)
        elif ksat == 1:
            return _prop(x = x, p = var1, e = var2, Dliq = _Dliq.value,
                          Dvap = _Dvap.value, xliq = xliq, xvap = xvap,
                          q = _q.value, t = _t.value, tbub = _tbub.value,
                          tdew = _tdew.value, Dlbub = _Dlbub.value,
                          Dvdew = _Dvdew.value, xbub = xbub, xdew = xdew,
                          ierr = _ierr.value, herr = _herr.value, ksat = ksat,
                          defname = defname)
    elif routine.upper() == u'TQ':
        if ksat == 0:
            return _prop(x = x, t = var1, q = var2, Dliq = _Dliq.value,
                          kq = kq, Dvap = _Dvap.value, xliq = xliq, xvap = xvap,
                          p = _p.value, ierr = _ierr.value, herr = _herr.value,
                          pbub = _pbub.value, pdew = _pdew.value,
                          Dlbub = _Dlbub.value, Dvdew = _Dvdew.value,
                          xbub = xbub, xdew = xdew, ksat = ksat,
                          defname = defname)
        elif ksat == 1:
            return _prop(x = x, t = var1, q = var2, Dliq = _Dliq.value,
                          kq = kq, Dvap = _Dvap.value, xliq = xliq, xvap = xvap,
                          p = _p.value, pbub = _pbub.value, pdew = _pdew.value,
                          Dlbub = _Dlbub.value, Dvdew = _Dvdew.value,
                          xbub = xbub, xdew = xdew, ierr = _ierr.value,
                          herr = _herr.value, ksat = ksat, defname = defname)
    elif routine.upper() == u'PQ':
        if ksat == 0:
            return _prop(x = x, p = var1, q = var2, Dliq = _Dliq.value,
                          kq = kq, Dvap = _Dvap.value, xliq = xliq, xvap = xvap,
                          t = _t.value, ierr = _ierr.value, herr = _herr.value,
                          tbub = _tbub.value, tdew = _tdew.value,
                          Dlbub = _Dlbub.value, Dvdew = _Dvdew.value,
                          xbub = xbub, xdew = xdew, ksat = ksat,
                          defname = defname)
        elif ksat == 1:
            return _prop(x = x, p = var1, q = var2, Dliq = _Dliq.value,
                          kq = kq, Dvap = _Dvap.value, xliq = xliq, xvap = xvap,
                          t = _t.value, tbub = _tbub.value, tdew = _tdew.value,
                          Dlbub = _Dlbub.value, Dvdew = _Dvdew.value,
                          xbub = xbub, xdew = xdew, ierr = _ierr.value,
                          herr = _herr.value, ksat = ksat, defname = defname)
    #~ elif routine.upper() == 'DQ':
        #~ return _prop(x = x, D = var1, q = var2, Dliq = _Dliq.value, kq = kq,
                #~ Dvap = _Dvap.value, xliq = xliq, xvap = xvap, t = _t.value,
                #~ p = _p.value, ierr = _ierr.value, herr = _herr.value, defname = defname)


def _abfl2(routine, var1, var2, x, kq=1, ksat=0, tbub=0, tdew=0, pbub=0,
    pdew=0, Dlbub=0, Dvdew=0, xbub=None, xdew=None):
    u'''General flash calculation given two inputs and composition.  Valid
    properties for the first input are temperature and pressure.  Valid
    properties for the second input are density, energy, enthalpy, entropy,
    or quality.  The character string ab specifies the inputs.  Note that
    the input TP is not allowed here, but is done by calling TPFLSH or
    TPFL2.

    This routine calls TPFL2 within a secant-method iteration for
    pressure to find a solution.  Initial guesses are based on liquid
    density at the bubble point and vapor density at the dew point.

    inputs:
        routine--character*2 string defining the inputs, e.g., 'TD' or 'PQ'
        var1--first property (either temperature or pressure)
        var2--second property (density, energy, enthalpy, entropy, or quality)
        x--overall (bulk) composition [array of mol frac]
        kq--flag specifying units for input quality when b=quality
            kq = 1 [default] quality on MOLAR basis [moles vapor/total moles]
            kq = 2 quality on MASS basis [mass vapor/total mass]
        ksat--flag for bubble and dew point limits
            0 [default] = dew and bubble point limits computed here
            1 = must provide values for the following:
                (for a=pressure):
                    tbub--bubble point temperature [K] at (p,x=z)
                    tdew--dew point temperature [K] at (p,y=z)
                (for a=temperature):
                    pbub--bubble point pressure [kPa] at (t,x=z)
                    pdew--dew point pressure [kPa] at (t,y=z)
                (for either case):
                    Dlbub--liquid density [mol/L] at bubble point
                    Dvdew--vapor density [mol/L] at dew point
                    xbub--vapor composition [array of mol frac] at bubble point
                    xdew--liquid composition [array of mol frac] at dew point

    outputs:
        t--temperature [K]
        p--pressure [kPa]
        D--molar density [mol/L]
        Dliq--molar density [mol/L] of the liquid phase
        Dvap--molar density [mol/L] of the vapor phase
        xliq--composition of liquid phase [array of mol frac]
        xvap--composition of vapor phase [array of mol frac]
        q--vapor quality on a MOLAR basis [moles vapor/total moles]'''

    defname = u'_abfl2'

    _inputerrorcheck(locals())
    for each in xrange(len(x)):
        _x[each] = x[each]
        if xdew:
            for each in xrange(len(xdew)): _xdew[each] = xdew[each]
        if xbub:
            for each in xrange(len(xbub)): _xbub[each] = xbub[each]
    _ksat.value, _tbub.value, _kq.value = ksat, tbub, kq
    _tdew.value, _pbub.value, _pdew.value = tdew, pbub, pdew
    _Dlbub.value, _Dvdew.value = Dlbub, Dvdew
    _var1.value, _var2.value = var1, var2
    _routine.value = routine.upper().encode(u'ascii')

    _rpabfl2_(byref(_var1), byref(_var2), _x, byref(_kq), byref(_ksat),
               byref(_routine), byref(_tbub), byref(_tdew), byref(_pbub),
               byref(_pdew), byref(_Dlbub), byref(_Dvdew), _xbub, _xdew,
               byref(_t), byref(_p), byref(_Dliq), byref(_Dvap), _xliq,
               _xvap, byref(_q), byref(_ierr), byref(_herr), c_long(2), c_long(255))

    #define various x values
    xliq = normalize([_xliq[each] for each in xrange(_nc_rec.record)])[u'x']
    xvap = normalize([_xvap[each] for each in xrange(_nc_rec.record)])[u'x']
    xdew = normalize([_xdew[each] for each in xrange(_nc_rec.record)])[u'x']
    xbub = normalize([_xbub[each] for each in xrange(_nc_rec.record)])[u'x']
    if u'_purefld_rec' in _Setuprecord.object_list \
    and len(x) == 1:
        if len(x) != len(xliq):
            xliq = [xliq[_purefld_rec.record[u'icomp'] - 1]]
        if len(x) != len(xvap):
            xvap = [xvap[_purefld_rec.record[u'icomp'] - 1]]
        if len(x) != len(xdew):
            xdew = [xdew[_purefld_rec.record[u'icomp'] - 1]]
        if len(x) != len(xbub):
            xbub = [xbub[_purefld_rec.record[u'icomp'] - 1]]

    #Dvap and Dliq
    Dvap, Dliq = _Dvap.value, _Dliq.value
    #define q
    if routine.upper()[1] == u'Q':
        q = var2
    else:
        q = _q.value

    #calculate D
    if routine.upper()[1] == u'D':
        D = var2
    else:
        if Dliq == 0:
            D = Dvap
        elif Dvap == 0:
            D = Dliq
        else:
            D = 1 / (((1 / Dvap) * q) + ((1 / Dliq) * (1 - q)))

    #raise error if routine input is incorrect
    if not routine.upper()[0] in u'PT':
        raise RefpropinputError(u'Incorrect "routine" input, ' + unicode(routine) +
                                 u' is an invalid input')
    if not routine.upper()[1] in u'DEHSQ':
        raise RefpropinputError(u'Incorrect "routine" input, ' + unicode(routine) +
                                 u' is an invalid input')

    #return correction on the first input variable
    if routine.upper()[0] == u'P':
        #return correction on the second input variable
        if routine.upper()[1] == u'S':
            return _prop(x = x, t = _t.value, p = var1, s = var2, D = D, q = q,
                          Dliq = Dliq, Dvap = Dvap, xliq = xliq, xbub = xbub,
                          xvap = xvap, ksat = ksat, kq = kq,
                          ierr = _ierr.value, herr = _herr.value,
                          Dlbub = _Dlbub.value, Dvdew = _Dvdew.value,
                          xdew = xdew, tbub = _tbub.value, tdew = _tdew.value,
                          defname = defname)
        elif routine.upper()[1] == u'H':
            return _prop(x = x, t = _t.value, p = var1, h = var2, D = D, q = q,
                          Dliq = Dliq, Dvap = Dvap, xliq = xliq, xbub = xbub,
                          xvap = xvap, ksat = ksat, kq = kq,
                          ierr = _ierr.value, herr = _herr.value,
                          Dlbub = _Dlbub.value, Dvdew = _Dvdew.value,
                          xdew = xdew, tbub = _tbub.value, tdew = _tdew.value,
                          defname = defname)
        elif routine.upper()[1] == u'D':
            return _prop(x = x, t = _t.value, p = var1, D = var2, q = q,
                          Dliq = Dliq, Dvap = Dvap, xliq = xliq, xbub = xbub,
                          xvap = xvap, ksat = ksat, kq = kq,
                          ierr = _ierr.value, herr = _herr.value,
                          Dlbub = _Dlbub.value, Dvdew = _Dvdew.value,
                          xdew = xdew, tbub = _tbub.value, tdew = _tdew.value,
                          defname = defname)
        elif routine.upper()[1] == u'E':
            return _prop(x = x, t = _t.value, p = var1, e = var2, D = D, q = q,
                          Dliq = Dliq, Dvap = Dvap, xliq = xliq, xbub = xbub,
                          xvap = xvap, ksat = ksat, kq = kq,
                          ierr = _ierr.value, herr = _herr.value,
                          Dlbub = _Dlbub.value, Dvdew = _Dvdew.value,
                          xdew = xdew, tbub = _tbub.value, tdew = _tdew.value,
                          defname = defname)
        elif routine.upper()[1] == u'Q':
            return _prop(x = x, t = _t.value, p = var1, D = D, q = q,
                          Dliq = Dliq, Dvap = Dvap, xliq = xliq, xbub = xbub,
                          xvap = xvap, ksat = ksat, kq = kq,
                          ierr = _ierr.value, herr = _herr.value,
                          Dlbub = _Dlbub.value, Dvdew = _Dvdew.value,
                          xdew = xdew, tbub = _tbub.value, tdew = _tdew.value,
                          defname = defname)
    elif routine.upper()[0] == u'T':
        #return correction on the second input variable
        if routine.upper()[1] == u'S':
            return _prop(x = x, t = var1, p = _p.value, s = var2, D = D, q = q,
                          Dliq = Dliq, Dvap = Dvap, xliq = xliq, xbub = xbub,
                          xvap = xvap, ksat = ksat, kq = kq,
                          ierr = _ierr.value, herr = _herr.value,
                          pbub = _pbub.value, pdew = _pdew.value,
                          Dlbub = _Dlbub.value, Dvdew = _Dvdew.value,
                          xdew = xdew, defname = defname)
        elif routine.upper()[1] == u'H':
            return _prop(x = x, t = var1, p = _p.value, h = var2, D = D, q = q,
                          Dliq = Dliq, Dvap = Dvap, xliq = xliq, xbub = xbub,
                          xvap = xvap, ksat = ksat, kq = kq,
                          ierr = _ierr.value, herr = _herr.value,
                          pbub = _pbub.value, pdew = _pdew.value,
                          Dlbub = _Dlbub.value, Dvdew = _Dvdew.value,
                          xdew = xdew, defname = defname)
        elif routine.upper()[1] == u'D':
            return _prop(x = x, t = var1, p = _p.value, D = var2, q = q,
                          Dliq = Dliq, Dvap = Dvap, xliq = xliq, xbub = xbub,
                          xvap = xvap, ksat = ksat, kq = kq,
                          ierr = _ierr.value, herr = _herr.value,
                          pbub = _pbub.value, pdew = _pdew.value,
                          Dlbub = _Dlbub.value, Dvdew = _Dvdew.value,
                          xdew = xdew, defname = defname)
        elif routine.upper()[1] == u'E':
            return _prop(x = x, t = var1, p = _p.value, e = var2, D = D, q = q,
                          Dliq = Dliq, Dvap = Dvap, xliq = xliq, xbub = xbub,
                          xvap = xvap, ksat = ksat, kq = kq,
                          ierr = _ierr.value, herr = _herr.value,
                          pbub = _pbub.value, pdew = _pdew.value,
                          Dlbub = _Dlbub.value, Dvdew = _Dvdew.value,
                          xdew = xdew, defname = defname)
        elif routine.upper()[1] == u'Q':
            return _prop(x = x, t = var1, p = _p.value, D = D, q = var2,
                          Dliq = Dliq, Dvap = Dvap, xliq = xliq, xbub = xbub,
                          xvap = xvap, ksat = ksat, kq = kq,
                          ierr = _ierr.value, herr = _herr.value,
                          pbub = _pbub.value, pdew = _pdew.value,
                          Dlbub = _Dlbub.value, Dvdew = _Dvdew.value,
                          xdew = xdew, defname = defname)


def info(icomp=1):
    u'''Provides fluid constants for specified component

    input:
        icomp--component number in mixture; 1 for pure fluid
    outputs:
        wmm--molecular weight [g/mol]
        ttrp--triple point temperature [K]
        tnbpt--normal boiling point temperature [K]
        tcrit--critical temperature [K]
        pcrit--critical pressure [kPa]
        Dcrit--critical density [mol/L]
        zcrit--compressibility at critical point [pc/(Rgas*Tc*Dc)]
        acf--accentric factor [-]
        dip--dipole moment [debye]
        Rgas--gas constant [J/mol-K]'''
    _inputerrorcheck(locals())
    _icomp.value = icomp

    _rpinfo_(byref(_icomp), byref(_wmm), byref(_ttrp), byref(_tnbpt),
                  byref(_tcrit), byref(_pcrit), byref(_Dcrit), byref(_zcrit),
                  byref(_acf), byref(_dip), byref(_Rgas))

    return _prop(icomp = icomp, wmm = _wmm.value, ttrp = _ttrp.value,
            tnbpt = _tnbpt.value, tcrit = _tcrit.value, Dcrit = _Dcrit.value,
            zcrit = _zcrit.value, acf = _acf.value, dip = _dip.value,
            Rgas = _Rgas.value)


def rmix2(x):
    u'''Return the gas "constant" as a combination of the gas constants for
    the pure fluids

    inputs:
        x--composition [array of mol frac]
    outputs:
        Rgas--gas constant [J/mol-K]'''
    _inputerrorcheck(locals())
    for each in xrange(len(x)): _x[each] = x[each]

    _rprmix2_(_x, byref(_Rgas))

    return _prop(x = x, Rgas = _Rgas.value)


def xmass(x):
    u'''Converts composition on a mole fraction basis to mass fraction

    input:
        x--composition array [array of mol frac]
    outputs:
        xkg--composition array [array of mass frac]
        wmix--molar mass of the mixture [g/mol], a.k.a. "molecular weight"'''
    _inputerrorcheck(locals())
    for each in xrange(len(x)): _x[each] = x[each]

    _rpxmass_(_x, _xkg, byref(_wmix))

    xkg = normalize([_xkg[each] for each in xrange(_nc_rec.record)])[u'x']
    if u'_purefld_rec' in _Setuprecord.object_list \
    and len(x) == 1:
        if len(x) != len(xkg):
            xkg = [xkg[_purefld_rec.record[u'icomp'] - 1]]
    return _prop(x = x, xkg = xkg, wmix = _wmix.value)


def xmole(xkg):
    u'''Converts composition on a mass fraction basis to mole fraction

    input:
        xkg--composition array [array of mass frac]
    outputs:
        x--composition array [array of mol frac]
        wmix--molar mass of the mixture [g/mol], a.k.a. "molecular weight"'''
    _inputerrorcheck(locals())
    for each in xrange(len(xkg)): _xkg[each] = xkg[each]
    
    _rpxmole_(_xkg, _x, byref(_wmix))

    x = normalize([_x[each] for each in xrange(_nc_rec.record)])[u'x']
    if u'_purefld_rec' in _Setuprecord.object_list \
    and len(xkg) == 1:
        if len(xkg) != len(x):
            x = [x[_purefld_rec.record[u'icomp'] - 1]]
    return _prop(xkg = xkg, x = x, wmix = _wmix.value)


def limitx(x, htype=u'EOS', t=0, D=0, p=0):
    u'''returns limits of a property model as a function of composition
    and/or checks input t, D, p against those limits

    Pure fluid limits are read in from the .FLD files; for mixtures, a
    simple mole fraction weighting in reduced variables is used.

    Attempting calculations below the mininum temperature and/or above the
    maximum density will result in an error. These will often correspond to
    a physically unreasonable state; also many equations of state do not
    extrapolate reliably to lower T's and higher D's.

    A warning is issued if the temperature is above the maximum but below
    1.5 times the maximum; similarly pressures up to twice the maximum
    result in only a warning. Most equations of state may be extrapolated to
    higher T's and P's. Temperatures and/or pressures outside these extended
    limits will result in an error.

    When calling with an unknown temperature, set t to -1 to avoid
    performing the melting line check

    inputs:
        x--composition array [mol frac]
        htype--flag indicating which models are to be checked [character*3]
            'EOS':  equation of state for thermodynamic properties
            'ETA':  viscosity
            'TCX':  thermal conductivity
            'STN':  surface tension
        t--temperature [K]
        D--molar density [mol/L]
        p--pressure [kPa]
            N.B.--all inputs must be specified, if one or more are not
            available, (or not applicable as in case of surface tension)
            use reasonable values, such as:
                t = tnbp
                D = 0
                p = 0
    outputs:
        tmin--minimum temperature for model specified by htyp [K]
        tmax--maximum temperature [K]
        Dmax--maximum density [mol/L]
        pmax--maximum pressure [kPa]'''

    _inputerrorcheck(locals())
    _htype.value = htype.upper().encode(u'ascii')
    for each in xrange(len(x)): _x[each] = x[each]
    _t.value, _D.value, _p.value = t, D, p
    
    _rplimitx_(byref(_htype), byref(_t), byref(_D), byref(_p), _x,
                byref(_tmin), byref(_tmax), byref(_Dmax), byref(_pmax),
                byref(_ierr), byref(_herr), c_long(3), c_long(255))

    return _prop(x = x, t = t, D = D, htype = htype.upper(), p = p,
                  tmin = _tmin.value, tmax = _tmax.value, Dmax = _Dmax.value,
                  pmax = _pmax.value, ierr = _ierr.value, herr = _herr.value,
                  defname = u'limitx')


def limitk(htype=u'EOS', icomp=1, t=u'tnbp', D=0, p=0):
    u'''Returns limits of a property model (read in from the .FLD files) for
    a mixture component and/or checks input t, D, p against those limits

    This routine functions in the same manner as LIMITX except that the
    composition x is replaced by the component number icomp.

    Attempting calculations below the minimum temperature and/or above the
    maximum density will result in an error. These will often correspond to
    a physically unreasonable state; also many equations of state do not
    extrapolate reliably to lower T's and higher D's.

    A warning is issued if the temperature is above the maximum but below
    1.5 times the maximum; similarly pressures up to twice the maximum
    result in only a warning. Most equations of state may be extrapolated to
    higher T's and P's. Temperatures and/or pressures outside these extended
    limits will result in an error.

    inputs:
        htyp--flag indicating which models are to be checked [character*3]
            'EOS':  equation of state for thermodynamic properties
            'ETA':  viscosity
            'TCX':  thermal conductivity
            'STN':  surface tension
        icomp--component number in mixture; 1 for pure fluid
        t--temperature [K]
        D--molar density [mol/L]
        p--pressure [kPa]
            N.B.--all inputs must be specified, if one or more are not
            available, (or not applicable as in case of surface tension) use
            reasonable values, such as:
                t = tnbp (normal boiling point temperature)
                D = 0
                p = 0
    outputs:
        tmin--minimum temperature for model specified by htyp [K]
        tmax--maximum temperature [K]
        Dmax--maximum density [mol/L]
        pmax--maximum pressure [kPa]'''
    if t == u'tnbp':
        t = info(icomp)[u'tnbpt']

    _inputerrorcheck(locals())
    _htype.value = htype.upper().encode(u'ascii')
    _icomp.value = icomp
    _t.value, _D.value, _p.value = t, D, p

    _rplimitk_(byref(_htype), byref(_icomp), byref(_t), byref(_D),
                byref(_p), byref(_tmin), byref(_tmax), byref(_Dmax),
                byref(_pmax), byref(_ierr), byref(_herr), c_long(3), c_long(255))

    return _prop(icomp = icomp, t = t, D = D, htype = htype.upper(),
            p = p, tmin = _tmin.value, tmax = _tmax.value,
            Dmax = _Dmax.value, pmax = _pmax.value, ierr = _ierr.value,
            herr = _herr.value, defname = u'limitl')


def limits(x, htype=u'EOS'):
    u'''Returns limits of a property model as a function of composition.

    Pure fluid limits are read in from the .FLD files; for mixtures, a
    simple mole fraction weighting in reduced variables is used.

    inputs:
        htype--flag indicating which models are to be checked [character*3]
            'EOS':  equation of state for thermodynamic properties
            'ETA':  viscosity
            'TCX':  thermal conductivity
            'STN':  surface tension
        x--composition array [mol frac]
    outputs:
        tmin--minimum temperature for model specified by htyp [K]
        tmax--maximum temperature [K]
        Dmax--maximum density [mol/L]
        pmax--maximum pressure [kPa]'''
    _inputerrorcheck(locals())
    _htype.value = htype.upper().encode(u'ascii')
    for each in xrange(len(x)): _x[each] = x[each]

    _rplimits_(byref(_htype), _x, byref(_tmin), byref(_tmax), byref(_Dmax),
                byref(_pmax), c_long(3))

    return _prop(x = x,
            htype = htype.upper(), tmin = _tmin.value, tmax = _tmax.value,
            Dmax = _Dmax.value, pmax = _pmax.value)


def qmass(q, xliq, xvap):
    u'''converts quality and composition on a mole basis to a mass basis

    inputs:
        q--molar quality [moles vapor/total moles]
            qmol = 0 indicates saturated liquid
            qmol = 1 indicates saturated vapor
            0 < qmol < 1 indicates a two-phase state
            mol < 0 or qmol > 1 are not allowed and will result in warning
        xliq--composition of liquid phase [array of mol frac]
        xvap--composition of vapor phase [array of mol frac]
    outputs:
        qkg--quality on mass basis [mass of vapor/total mass]
        xlkg--mass composition of liquid phase [array of mass frac]
        xvkg--mass composition of vapor phase [array of mass frac]
        wliq--molecular weight of liquid phase [g/mol]
        wvap--molecular weight of vapor phase [g/mol]'''
    _inputerrorcheck(locals())
    _q.value = q
    for each in xrange(len(xliq)):
        _xliq[each] = xliq[each]
    for each in xrange(len(xvap)):
        _xvap[each] = xvap[each]
    
    _rpqmass_(byref(_q), _xliq, _xvap, byref(_qkg), _xlkg, _xvkg,
               byref(_wliq), byref(_wvap), byref(_ierr), byref(_herr), c_long(255))

    xlkg = normalize([_xlkg[each] for each in xrange(_nc_rec.record)])[u'x']
    xvkg = normalize([_xvkg[each] for each in xrange(_nc_rec.record)])[u'x']
    if u'_purefld_rec' in _Setuprecord.object_list \
    and (len(xliq) == 1 or len(xvap) == 1):
        if len(xliq) != len(xlkg):
            xlkg = [xlkg[_purefld_rec.record[u'icomp'] - 1]]
        if len(xvap) != len(xvkg):
            xvkg = [xvkg[_purefld_rec.record[u'icomp'] - 1]]
    return _prop(q = q, xliq = xliq, xvap = xvap, qkg = _qkg.value, xlkg = xlkg,
            xvkg = xvkg, wliq = _wliq.value, wvap = _wvap.value,
            ierr = _ierr.value, herr = _herr.value, defname = u'qmass')


def qmole(qkg, xlkg, xvkg):
    u'''Converts quality and composition on a mass basis to a molar basis.

    inputs:
        qkg--quality on mass basis [mass of vapor/total mass]
            qkg = 0 indicates saturated liquid
            qkg = 1 indicates saturated vapor
            0 < qkg < 1 indicates a two-phase state
            qkg < 0 or qkg > 1 are not allowed and will result in warning
        xlkg--mass composition of liquid phase [array of mass frac]
        xvkg--mass composition of vapor phase [array of mass frac]
    outputs:
        q--quality on mass basis [mass of vapor/total mass]
        xliq--molar composition of liquid phase [array of mol frac]
        xvap--molar composition of vapor phase [array of mol frac]
        wliq--molecular weight of liquid phase [g/mol]
        wvap--molecular weight of vapor phase [g/mol]'''

    _inputerrorcheck(locals())
    _qkg.value = qkg
    for each in xrange(len(xlkg)):
        _xlkg[each] = xlkg[each]
    for each in xrange(len(xvkg)):
        _xvkg[each] = xvkg[each]
    
    _rpqmole_(byref(_qkg), _xlkg, _xvkg, byref(_q), _xliq, _xvap,
               byref(_wliq), byref(_wvap), byref(_ierr), byref(_herr), c_long(255))

    xliq = normalize([_xliq[each] for each in xrange(_nc_rec.record)])[u'x']
    xvap = normalize([_xvap[each] for each in xrange(_nc_rec.record)])[u'x']
    if u'_purefld_rec' in _Setuprecord.object_list \
    and (len(xlkg) == 1 or len(xvkg) == 1):
        if len(xlkg) != len(xliq):
            xliq = [xliq[_purefld_rec.record[u'icomp'] - 1]]
        if len(xvkg) != len(xvap):
            xvap = [xvap[_purefld_rec.record[u'icomp'] - 1]]
    return _prop(qkg = qkg, xlkg = xlkg, xvkg = xvkg, q = _q.value, xliq = xliq,
            xvap = xvap, wliq = _wliq.value, wvap = _wvap.value,
            ierr = _ierr.value, herr = _herr.value, defname = u'qmole')


def wmol(x):
    u'''Molecular weight for a mixture of specified composition

    input:
        x--composition array [array of mol frac]
    output (as function value):
        wmix--molar mass [g/mol], a.k.a. "molecular weight'''
    _inputerrorcheck(locals())
    for each in xrange(len(x)): _x[each] = x[each]

    _rpwmoldll_(_x, byref(_wmix))

    return _prop(x = x, wmix = _wmix.value)


def dielec(t, D, x):
    u'''Compute the dielectric constant as a function of temperature,
    density, and composition.

    inputs:
        t--temperature [K]
        d--molar density [mol/L]
        x--composition [array of mol frac]
    output:
        de--dielectric constant'''
    _inputerrorcheck(locals())
    _t.value, _D.value = t, D
    for each in xrange(len(x)): _x[each] = x[each]
    
    _rpdielec_(byref(_t), byref(_D), _x, byref(_de))

    return _prop(x = x, t = t, D= D, de = _de.value)


def surft(t, x):
    u'''Compute surface tension

    inputs:
        t--temperature [K]
        x--composition [array of mol frac] (liquid phase input only)
    outputs:
        D--molar density of liquid phase [mol/L]
            if D > 0 use as input value
            < 0 call SATT to find density
        sigma--surface tension [N/m]'''

    _inputerrorcheck(locals())
    _t.value = t
    for each in xrange(len(x)): _x[each] = x[each]
    
    _rpsurft_(byref(_t), byref(_D), _x, byref(_sigma), byref(_ierr),
               byref(_herr), c_long(255))

    return _prop(x = x, t = t, D = _D.value, sigma = _sigma.value,
                    ierr = _ierr.value, herr = _herr.value, defname = u'surft')


def surten(t, Dliq, Dvap, xliq, xvap):
    u'''Compute surface tension

    inputs:
        t--temperature [K]
        Dliq--molar density of liquid phase [mol/L]
        Dvap--molar density of vapor phase [mol/L]
            if either Dliq or Dvap < 0 call SATT to find densities
        xliq--composition of liquid phase [array of mol frac]
        xvap--composition of liquid phase [array of mol frac]
            (xvap is optional input if Dliq < 0 or Dvap < 0)
    outputs:
        sigma--surface tension [N/m]'''

    _inputerrorcheck(locals())
    _t.value, _Dliq.value, _Dvap.value = t, Dliq, Dvap
    for each in xrange(len(xliq)):
        _xliq[each] = xliq[each]
    for each in xrange(len(xvap)):
        _xvap[each] = xvap[each]
    
    _rpsurten_(byref(_t), byref(_Dliq), byref(_Dvap), _xliq, _xvap,
                byref(_sigma), byref(_ierr), byref(_herr), c_long(255))

    return _prop(t = t, Dliq = Dliq, Dvap = Dvap, xliq = xliq, xvap = xvap,
            sigma = _sigma.value, ierr = _ierr.value, herr = _herr.value,
            defname = u'surten')


def meltt(t, x):
    u'''Compute the melting line pressure as a function of temperature and
    composition.

    inputs:
        t--temperature [K]
        x--composition [array of mol frac]
    output:
        p--melting line pressure [kPa]

    Caution
        if two valid outputs the function will returns the highest'''

    _inputerrorcheck(locals())
    _t.value = t
    for each in xrange(len(x)): _x[each] = x[each]
    
    _rpmeltt_(byref(_t), _x, byref(_p), byref(_ierr), byref(_herr), c_long(255))

    return _prop(t = t, x = x, p = _p.value, ierr = _ierr.value,
                        herr = _herr.value, defname = u'meltt')


def meltp(p, x):
    u'''Compute the melting line temperature as a function of pressure and
    composition.

    inputs:
        p--melting line pressure [kPa]
        x--composition [array of mol frac]
    output:
        t--temperature [K]'''

    _inputerrorcheck(locals())
    _p.value = p
    for each in xrange(len(x)): _x[each] = x[each]

    _rpmeltp_(byref(_p), _x, byref(_t), byref(_ierr), byref(_herr), c_long(255))
    
    return _prop(p = p, x = x, t = _t.value, ierr = _ierr.value,
                    herr = _herr.value, defname = u'meltp')


def sublt(t, x):
    u'''Compute the sublimation line pressure as a function of temperature
    and composition.

    inputs:
        t--temperature [K]
        x--composition [array of mol frac]
    output:
        p--sublimation line pressure [kPa]'''

    _inputerrorcheck(locals())
    _t.value = t
    for each in xrange(len(x)): _x[each] = x[each]
    
    _rpsublt_(byref(_t), _x, byref(_p), byref(_ierr), byref(_herr), c_long(255))

    return _prop(t = t, x = x, p = _p.value, ierr = _ierr.value,
            herr = _herr.value, defname = u'sublt')


def sublp(p, x):
    u'''Compute the sublimation line temperature as a function of pressure
    and composition.

    inputs:
        p--melting line pressure [kPa]
        x--composition [array of mol frac]
    output:
        t--temperature [K]'''

    _inputerrorcheck(locals())
    _p.value = p
    for each in xrange(len(x)): _x[each] = x[each]

    _rpsublp_(byref(_p), _x, byref(_t), byref(_ierr), byref(_herr), c_long(255))

    return _prop(p = p, x = x, t = _t.value, ierr = _ierr.value,
                    herr = _herr.value, defname = u'sublp')


def trnprp(t, D, x):
    u'''Compute the transport properties of thermal conductivity and
    viscosity as functions of temperature, density, and composition

    inputs:
        t--temperature [K]
        D--molar density [mol/L]
        x--composition array [mol frac]
    outputs:
        eta--viscosity (uPa.s)
        tcx--thermal conductivity (W/m.K)'''

    _inputerrorcheck(locals())
    _t.value, _D.value = t, D
    for each in xrange(len(x)): _x[each] = x[each]
    
    _rptrnprp_(byref(_t), byref(_D), _x, byref(_eta), byref(_tcx),
                byref(_ierr), byref(_herr), c_long(255))

    return _prop(x = x, D = D, t = t, eta = _eta.value, tcx = _tcx.value,
            ierr = _ierr.value, herr = _herr.value, defname = u'trnprp')


def getktv(icomp, jcomp):
    u'''Retrieve mixture model and parameter info for a specified binary

    This subroutine should not be called until after a call to SETUP.

    inputs:
        icomp--component i
        jcomp--component j
    outputs:
        hmodij--mixing rule for the binary pair i,j (e.g. LJ1 or LIN)
            [character*3]
        fij--binary mixture parameters [array of dimension nmxpar;
            currently nmxpar is set to 6]; the parameters will vary depending
            on hmodij;
        hfmix--file name [character*255] containing parameters for the binary
            mixture model
        hfij--description of the binary mixture parameters [character*8 array
            of dimension nmxpar] for example, for the Lemmon-Jacobsen model
            (LJ1):
                fij(1) = zeta
                fij(2) = xi
                fij(3) = Fpq
                fij(4) = beta
                fij(5) = gamma
                fij(6) = 'not used'
        hbinp--documentation for the binary parameters [character*255]
            terminated with ASCII null character
        hmxrul--description of the mixing rule [character*255]'''
    _inputerrorcheck(locals())
    _icomp.value, _jcomp.value = icomp, jcomp
    
    _rpgetktv_(byref(_icomp), byref(_jcomp), byref(_hmodij), _fij,
                byref(_hfmix), _hfij, byref(_hbinp), byref(_hmxrul), c_long(3), c_long(255),
                c_long(8), c_long(255), c_long(255))

    return _prop(icomp = icomp, jcomp = jcomp,
            hmodij = _hmodij.value.decode(u'utf-8'),
            fij = [_fij[each] for each in xrange(_nmxpar)],
            hfmix = _hfmix.value.decode(u'utf-8'),
            hbinp = _hbinp.value.decode(u'utf-8').rstrip(),
            hmxrul = _hmxrul.value.decode(u'utf-8').rstrip(),
            #correction on system error
            #hfij = [_hfij[each].value.decode('utf-8').strip()
            #         for each in range(_nmxpar)])
            hfij = [_hfij[0].value.decode(u'utf-8')[each * 8: each * 8 + 8].strip()
                      for each in xrange(_nmxpar)])


def getmod(icomp, htype):
    u'''Retrieve citation information for the property models used

    inputs:
        icomp--pointer specifying component number
            zero and negative values are used for ECS reference fluid(s)
        htype--flag indicating which model is to be retrieved [character*3]
            'EOS':  equation of state for thermodynamic properties
            'CP0':  ideal part of EOS (e.g. ideal-gas heat capacity)
            'ETA':  viscosity
            'VSK':  viscosity critical enhancement
            'TCX':  thermal conductivity
            'TKK':  thermal conductivity critical enhancement
            'STN':  surface tension
            'DE ':  dielectric constant
            'MLT':  melting line (freezing line, actually)
            'SBL':  sublimation line
            'PS ':  vapor pressure equation
            'DL ':  saturated liquid density equation
            'DV ':  saturated vapor density equation
    outputs:
        hcode--component model used for property specified in htype
            some possibilities for thermodynamic properties:
                'FEQ':  Helmholtz free energy model
                'BWR':  pure fluid modified Benedict-Webb-Rubin (MBWR)
                'ECS':  pure fluid thermo extended corresponding states
            some possibilities for viscosity:
                'ECS':  extended corresponding states (all fluids)
                'VS1':  the 'composite' model for R134a, R152a, NH3, etc.
                'VS2':  Younglove-Ely model for hydrocarbons
                'VS4':  generalized friction theory of Quinones-Cisneros and Dieters
                'VS5':  Chung et al model
            some possibilities for thermal conductivity:
                'ECS':  extended corresponding states (all fluids)
                'TC1':  the 'composite' model for R134a, R152a, etc.
                'TC2':  Younglove-Ely model for hydrocarbons
                'TC5':  predictive model of Chung et al. (1988)
            some possibilities for surface tension:
                'ST1':  surface tension as f(tau); tau = 1 - T/Tc
        hcite--component model used for property specified in htype;
            the first 3 characters repeat the model designation of hcode
            and the remaining are the citation for the source'''
    _inputerrorcheck(locals())
    _icomp.value, _htype.value = icomp, htype.upper().encode(u'ascii')

    _rpgetmod_(byref(_icomp), byref(_htype), byref(_hcode), byref(_hcite),
                c_long(3), c_long(3), c_long(255))

    return _prop(icomp = icomp, htype = htype,
                        hcode = _hcode.value.decode(u'utf-8'),
                        hcite = _hcite.value.decode(u'utf-8').rstrip())


def setktv(icomp, jcomp, hmodij, fij=([0] * _nmxpar), hfmix=u'HMX.BNC'):
    u'''Set mixture model and/or parameters

    This subroutine must be called after SETUP, but before any call to
    SETREF; it need not be called at all if the default mixture parameters
    (those read in by SETUP) are to be used.

    inputs:
        icomp--component
        jcomp--component j
        hmodij--mixing rule for the binary pair i,j [character*3] e.g.:
            'LJ1' (Lemmon-Jacobsen model)
            'LM1' (modified Lemmon-Jacobsen model) or
            'LIN' (linear mixing rules)
            'RST' indicates reset all pairs to values from original call to
                SETUP (i.e. those read from file) [all other inputs are
                ignored]
        fij--binary mixture parameters [array of dimension nmxpar; currently
            nmxpar is set to 6] the parameters will vary depending on hmodij;
            for example, for the Lemmon-Jacobsen model
                (LJ1):
                    fij(1) = zeta
                    fij(2) = xi
                    fij(3) = Fpq
                    fij(4) = beta
                    fij(5) = gamma
                    fij(6) = 'not used'
        hfmix--file name [character*255] containing generalized parameters
            for the binary mixture model; this will usually be the same as the
            corresponding input to SETUP (e.g.,':fluids:HMX.BNC')'''
    global _setktv_rec, _fpath, _setupprop

    #verify multiple model calls
    _checksetupmodel(u'setktv')

    _inputerrorcheck(locals())

    #define setup record for FluidModel
    if hmodij.upper() != u'RST':
        _setktv_rec = _Setuprecord(copy(locals()), u'_setktv_rec')

    _icomp.value, _jcomp.value = icomp, jcomp
    _hmodij.value = hmodij.upper().encode(u'ascii')
    if hfmix == u'HMX.BNC':
        _hfmix.value = (_fpath + u'fluids/HMX.BNC').encode(u'ascii')
    else: _hfmix.value = hfmix.encode(u'ascii')
    for each in xrange(_nmxpar): _fij[each] = fij[each]

    _rpsetktv_(byref(_icomp), byref(_jcomp), byref(_hmodij), _fij,
                byref(_hfmix), byref(_ierr), byref(_herr), c_long(3), c_long(255), c_long(255))

    if hmodij.upper() != u'RST':
        stktv = {}
        stktv[u'icomp'] = icomp
        stktv[u'jcomp'] = jcomp
        stktv[u'hmodij'] = hmodij.upper()
        stktv[u'fij'] = fij
        stktv[u'hfmix'] = hfmix
        _setupprop[u'setktv'] = stktv
    elif hmodij.upper() == u'RST':
        if u'setktv' in _setupprop:
            _setupprop.__delitem__(u'setktv')
        if u'_setktv_rec' in _Setuprecord.object_list:
            _setktv_rec = None

    return _prop(ierr = _ierr.value, herr = _herr.value, defname = u'setktv')


def setaga():
    u'''Set up working arrays for use with AGA8 equation of state.

    input:
        none
    outputs:
        none'''
    global _setaga_rec, _setupprop

    #verify multiple model calls
    _checksetupmodel(u'setaga')

    #define setup record for FluidModel
    _setaga_rec = _Setuprecord(copy(locals()), u'_setaga_rec')


    _rpsetaga_(byref(_ierr), byref(_herr), c_long(255))

    _setupprop[u'setaga'] = True
    return _prop(ierr = _ierr.value, herr = _herr.value, defname = u'setaga')


def unsetaga():
    u'''Load original values into arrays changed in the call to SETAGA.  This
    routine resets the values back to those loaded when SETUP was called.'''
    global _setaga_rec, _setupprop

    _rpunsetaga_()

    if u'setaga' in _setupprop:
        _setupprop.__delitem__(u'setaga')
    if u'_setaga_rec' in _Setuprecord.object_list:
        _setaga_rec = None
    return _prop()

def preos(ixflag=0):
    u'''Turn on or off the use of the PR cubic equation.

    inputs:
        ixflag--flag specifying use of PR:
            0 - Use full equation of state (Peng-Robinson off)
            1 - Use full equation of state with Peng-Robinson for sat. conditions
                (not currently working)
            2 - Use Peng-Robinson equation for all calculations
            -1 - return value with current usage of PR:  0, 1, or 2.'''
    #return value gives error return on preos
    global _preos_rec, _setupprop

    #verify multiple model calls
    _checksetupmodel(u'preos')

    _inputerrorcheck(locals())

    _ixflag.value = ixflag

    _rppreos_(byref(_ixflag))

    #return settings
    if ixflag == -1:
        #some unknown reason the value is less 2*32
        return _ixflag.value + 2**32
    #reset all preos values
    elif ixflag == 0:
        if u'preos' in _setupprop:
            _setupprop.__delitem__(u'preos')
        if u'_preos_rec' in _Setuprecord.object_list:
            _preos_rec = None
    else:
        _setupprop[u'preos'] = ixflag
        #define setup record for FluidModel
        _preos_rec = _Setuprecord({u'ixflag':ixflag}, u'_preos_rec')
        return _prop()

def getfij(hmodij):
    u'''Retrieve parameter info for a specified mixing rule

    This subroutine should not be called until after a call to SETUP.

    inputs:
        hmodij--mixing rule for the binary pair i,j (e.g. LJ1 or LIN)
            [character*3]
    outputs:
        fij--binary mixture parameters [array of dimension nmxpar; currently
            nmxpar is set to 6]; the parameters will vary depending on hmodij;
        hfij--description of the binary mixture parameters [character*8
            array of dimension nmxpar]
        hmxrul--description of the mixing rule [character*255]'''
    _inputerrorcheck(locals())
    _hmodij.value = hmodij.upper().encode(u'ascii')

    _rpgetfij_(byref(_hmodij), _fij, _hfij, byref(_hmxrul), c_long(3), c_long(8), c_long(255))

    return _prop(hmodij = hmodij.upper(),
            fij = [_fij[each] for each in xrange(_nmxpar)],
            hmxrul = _hmxrul.value.decode(u'utf-8').rstrip(),
            #correction on system error
            #hfij = [_hfij[each].value.decode('utf-8').strip()
            #         for each in range(_nmxpar)])
            hfij = [_hfij[0].value.decode(u'utf-8')[each * 8:each * 8 + 8].strip()
                      for each in xrange(_nmxpar)])


def b12(t, x):
    u'''Compute b12 as a function of temperature and composition.

    inputs:
        t--temperature [K]
        x--composition [array of mol frac]
    outputs:
        b--b12 [(L/mol)^2]'''
    _inputerrorcheck(locals())
    _t.value = t
    for each in xrange(len(x)): _x[each] = x[each]

    _rpb12_(byref(_t), _x, byref(_b))

    return _prop(t = t, x = x, b = _b.value)


def excess(t, p, x, kph=0):
    u'''Compute excess properties as a function of temperature, pressure, and
    composition.

    NOT supported on Windows

    inputs:
        t--temperature [K]
        p--pressure [kPa]
        x--composition [array of mol frac]
        kph--phase flag:
            1 = liquid
            2 = vapor
            0 = stable phase
    outputs:
        D--molar density [mol/L] (if input less than 0, used as initial guess)
        vE--excess volume [L/mol]
        eE--excess energy [J/mol]
        hE--excess enthalpy [J/mol]
        sE--excess entropy [J/mol-K]
        aE--excess Helmholtz energy [J/mol]
        gE--excess Gibbs energy [J/mol]'''
    _inputerrorcheck(locals())

    _t.value, _p.value, _kph.value = t, p, kph
    for each in xrange(len(x)): _x[each] = x[each]

    _rpexcess_(byref(_t), byref(_p), _x, byref(_kph), byref(_D), byref(_vE),
                byref(_eE), byref(_hE), byref(_sE), byref(_aE), byref(_gE),
                byref(_ierr), byref(_herr), c_long(255))

    return _prop(t = t, p = p, x = x, kph = kph, D = _D.value, vE = _vE.value,
            eE = _eE.value, hE = _hE.value, sE = _sE.value, aE = _aE.value,
            gE = _gE.value, ierr = _ierr.value, herr = _herr.value,
            defname = u'excess')


#def phiderv(icomp, jcomp, t, D, x): input values changed......................................
    #'''Calculate various derivatives needed for VLE determination

    #based on derivations in the GERG-2004 document for natural gas

    #inputs:
        #icomp--component number of which to take derivative
        #jcomp--component number of which to take derivative
        #t--temperature (K)
        #D--density (mol/L)
        #x--composition [array of mol frac]
    #outputs: (where n is mole number)
        #dadn--n*partial(alphar)/partial(ni)                     (Eq. 7.16 in GERG)
        #dnadn--partial(n*alphar)/partial(ni)                    (Eq. 7.15 in GERG)

        #dtdn--n*[partial(Tred)/partial(ni)]/Tred                (Eq. 7.19 in GERG)
        #dvdn--n*[partial(Vred)/partial(ni)]/Vred                (Eq. 7.18 in GERG)
            #(=-n*[partial(Dred)/partial(ni)]/Dred)
        #daddn--del*n*partial(darddel)/partial(ni)               (Eq. 7.17 in GERG)
            #where darddel=partial(alphar)/partial(del)
        #d2adnn--n*partial^2(n*alphar)/partial(ni)/partial(nj)   (Eq. 7.46 in GERG)
            #the following are at constant tau and/or del
        #dadxi--partial(alphar)/partial(xi)                      (Eq. 7.21g in GERG)
        #sdadxi--sum[xi*partial(alphar)/partial(xi)]             (Eq. 7.21g in GERG)
        #dadxij--partial^2(alphar)/partial(xi)/partial(xj)       (Eq. 7.21i in GERG)
        #daddx--del*partial^2(alphar)/partial(xi)/partial(del)   (Eq. 7.21j in GERG)
        #daddxii--del*partial^3(alphar)/partial(xi)/partial(xj)/partial(del)

    #other calculated variables:
        #d2addn--del*par.(n*(par.(alphar)/par.(n)/par.(del)      (Eq. 7.50 in GERG)
        #d2adtn--tau*par.(n*(par.(alphar)/par.(n)/par.(tau)      (Eq. 7.51 in GERG)
        #d2adxn--par.(n*(par.(alphar)/par.(n)/par.(xj)           (Eq. 7.52 in GERG)
    #'''
    #_inputerrorcheck(locals())
    #_icomp.value, _jcomp.value = icomp, jcomp
    #_t.value, _D.value = t, D
    #for each in range(len(x)): _x[each] = x[each]

    #_rpphiderv_(byref(_icomp), byref(_jcomp), byref(_t), byref(_D), _x,
                 #byref(_dadn), byref(_dnadn), byref(_ierr), byref(_herr),
                 #c_long(255))

    #return _prop(icomp = icomp, jcomp = jcomp, t = t, D = D, x = x,
            #dadn = _dadn.value, dnadn = _dnadn.value, ierr = _ierr.value,
            #herr = _herr.value, defname = 'phinderv')
u"""
calculate various derivatives needed for VLE determination
c  based on derivations in the GERG-2004 document for natural gas
c
c  inputs:
c        iderv--set to 1 for first order derivatives only (dadn and dnadn)
c               set to 2 for full calculations
c        t--temperature (K)
c      rho--density (mol/L)
c        x--composition [array of mol frac]
c
c  outputs: (where n is mole number)
c           (the listed equation numbers are those in the GERG manuscript)
c    dnadn--partial(n*alphar)/partial(ni)                   Eq. 7.15
c     dadn--n*partial(alphar)/partial(ni)                   Eq. 7.16
c    daddn--del*n*par.(par.(alphar)/par.(del))/par.(ni)     Eq. 7.17
c     dvdn--n*[partial(Vred)/partial(ni)]/Vred              Eq. 7.18
c           (=-n*[partial(Dred)/partial(ni)]/Dred)
c     dtdn--n*[partial(Tred)/partial(ni)]/Tred              Eq. 7.19
c    dadxi--partial(alphar)/partial(xi)                     Eq. 7.21g
c   sdadxi--sum[xi*partial(alphar)/partial(xi)]             Eq. 7.21g
c   dadxij--partial^2(alphar)/partial(xi)/partial(xj)       Eq. 7.21i
c    daddx--del*partial^2(alphar)/partial(xi)/partial(del)  Eq. 7.21j
c    dadtx--tau*partial^2(alphar)/partial(xi)/partial(tau)  Eq. 7.21k
c   dphidT--par.(ln(phi))/par.(T) (constant p,n,x)          Eq. 7.29
c   dphidp--par.(ln(phi))/par.(p) (constant T,n,x)          Eq. 7.30
c  dphidnj--n*par.[ln(phi(i))]/par(nj) (constant T,p)       Eq. 7.31
c  dlnfinidT--par.[ln(fi/ni)]/par(T)                        Eq. 7.36
c  dlnfinidV--n*par.[ln(fi/ni)]/par(V)                      Eq. 7.37
c   d2adbn--    par.[par.(n*alphar)/par.(ni)]/par.(T)       Eq. 7.44
c   d2adnn--n*partial^2(n*alphar)/partial(ni)/partial(nj)   Eq. 7.46 and 7.47 (similar to 7.38)
c   d2addn--del*par.[n*par.(alphar)/par.(ni)]/par.(del)     Eq. 7.50
c   d2adtn--tau*par.[n*par.(alphar)/par.(ni)]/par.(tau)     Eq. 7.51
c   d2adxn--    par.[n*par.(alphar)/par.(ni)]/par.(xj)      Eq. 7.52
c   ddrdxn--par.[n*par.(Dred)/par.(ni)]/par.(xj)            Eq. 7.55
c   dtrdxn--par.[n*par.(Tred)/par.(ni)]/par.(xj)            Eq. 7.56
c     dpdn--n*partial(p)/partial(ni)                        Eq. 7.63 constant T,V,nj
c    dpdxi--partial(p)/partial(xi)                          constant T,V
c d2adxnTV--par.[n*par.(alphar)/par.(ni)]/par.(xj)          constant T,V
c  dadxiTV--partial(alphar)/partial(xi)                     constant T,V
c daddxiTV--del*partial^2(alphar)/partial(xi)/partial(del)  constant T,V
c  dphidxj--par.(ln(phi))/par.(xj)                          constant T,p,x
c    xlnfi--Log of modified fugacity
"""

def cstar(t, p, v, x):
    u'''Calculate the critical flow factor, C*, for nozzle flow of a gas
    (subroutine was originally named CCRIT)

    inputs:
        t--temperature [K]
        p--pressure [kPa]
        v--plenum velocity [m/s] (should generally be set to 0 for
            calculating stagnation conditions)
        x--composition [array of mol frac]
    outputs:
        cs--critical flow factor [dimensionless]
        ts--nozzle throat temperature [K]
        Ds--nozzle throat molar density [mol/L]
        ps--nozzle throat pressure [kPa]
        ws--nozzle throat speed of sound [m/s]'''

    _inputerrorcheck(locals())
    _v.value = v
    _t.value, _p.value = t, p
    for each in xrange(len(x)): _x[each] = x[each]
    
    _rpcstar_(byref(_t), byref(_p), byref(_v), _x, byref(_cs), byref(_ts),
               byref(_Ds), byref(_ps), byref(_ws), byref(_ierr),
               byref(_herr), c_long(255))

    return _prop(t = t, p = p, v = v, x = x, cs = _cs.value, ts = _ts.value,
            Ds = _Ds.value, ps = _ps.value, ws = _ws.value, ierr = _ierr.value,
            herr = _herr.value, defname = u'cstar')


#compilations



#missing to do 
#SATTP
#CRTPNT
#SATGV
#MAXP
#DERVPVT
#DBDT2
#VIRBCD
#HEAT



u"""
      subroutine SATTP (t,p,x,iFlsh,iGuess,d,Dl,Dv,xliq,xvap,q,ierr,
     & herr)
c
c  Estimate temperature, pressure, and compositions to be used
c  as initial guesses to SATTP
c
c  inputs:
c   iFlsh--Phase flag:    0 - Flash calculation (T and P known)
c                         1 - T and xliq known, P and xvap returned
c                         2 - T and xvap known, P and xliq returned
c                         3 - P and xliq known, T and xvap returned
c                         4 - P and xvap known, T and xliq returned
c                         if this value is negative, the retrograde point will be returned
c        t--temperature [K] (input or output)
c        p--pressure [MPa] (input or output)
c        x--composition [array of mol frac]
c   iGuess--if set to 1, all inputs are used as initial guesses for the calculation
c  outputs:
c        d--overall molar density [mol/L]
c       Dl--molar density [mol/L] of saturated liquid
c       Dv--molar density [mol/L] of saturated vapor
c     xliq--liquid phase composition [array of mol frac]
c     xvap--vapor phase composition [array of mol frac]
c        q--quality
c     ierr--error flag:   0 = successful
c                         1 = unsuccessful
c     herr--error string (character*255 variable if ierr<>0)
c
c

broutine CRTPNT (z,tc,pc,rhoc,ierr,herr)
c
c     Subroutine for the determination of true critical point of a
c     mixture using the Method of Michelsen (1984)
c
c     The routine requires good initial guess values of pc and tc.
c     On convergence, the values of bb and cc should be close to zero
c     and dd > 0 for a two-phase critical point.
c     bb=0, cc=0 and dd <= 0 for an unstable critical point.
c
c  inputs:
c         z--composition [array of mol frac]
c
c  outputs:
c        tc--critical temperature [K]
c        pc--critical pressure [kPa]
c      rhoc--critical density [mol/l]
c      ierr--error flag
c      herr--error string (character*255 variable if ierr<>0)
c

     subroutine SATGV (t,p,z,vf,b,ipv,ityp,isp,rhox,rhoy,x,y,ierr,herr)
c
c  Calculates the bubble or dew point state using the entropy or density method
c  of GV.  The caculation method is similar to the volume based algorithm of GERG.
c  The cricondenbar and cricondentherm are estimated using the method in:  M.L.
c  Michelsen, Saturation point calculations, Fluid Phase Equilibria, 23:181, 1985.
c
c  inputs:
c         t--temperature [K]
c         p--pressure [kPa]
c         z--overall composition [array of mol frac]
c        vf--vapor fraction (0>=vf>=1)
c            set vf=0 for liquid and vf=1 for vapor
c            for ityp=6, vf=1 assumes x is liquid and y is vapor,
c                    and vf=0 assumes y is liquid and x is vapor
c         b--input value, either entropy [J/mol-K] or density [mol/l]
c       ipv--pressure or volume based algorithm
c            1 -> pressure based
c            2 -> volume based
c      ityp--input values
c            0 -> given p, calculate t
c            1 -> given t, calculate p
c            2 -> cricondentherm condition, calculate t,p (ipv=1 only)
c            3 -> cricondenbar condition, calculate t,p (ipv=1 only)
c            5 -> given entropy, calculate t,p
c            6 -> given density, calculate t,p
c       isp--use values from Splines as initial guesses if set to 1
c
c  outputs: (initial guesses must be sent in all variables (unless isp=1))
c         t--temperature [K]
c         p--pressure [kPa]
c      rhox--density of x phase [mol/l]
c      rhoy--density of y phase [mol/l]
c         x--composition of x array [array of mol frac]
c         y--composition of y array [array of mol frac]
c      ierr--error flag:  0 = successful
c                         1 = LUdecomp failed
c                         2 = derivatives are not available in RDXHMX
c                        71 = no convergence
c                        72 = log values too large
c                        73 = p or T out of range
c                        74 = trival solution
c                        75 = unacceptable F
c                        76 = False roots
c                        77 = density out of range
c                        80 = vf < 0 or vf > 1
c                        81 = sum(z)<>1
c                        82 = input rho<=0
c      herr--error string (character*255 variable if ierr<>0)
c
c
c  equations to be solved simultaneously are:
c  --pressure based:
c      f(1:n)=log(y/x)-log((fxi/nxi)/(fyi/nyi))=0
c      f(n+1)=sum(y(i)-x(i))=0
c      f(n+2)=b/binput-1=0, where b = p, t, d, or s
c
c  --volume based:
c      f(1:n) - log(y/x)-log((fxi/nxi)/(fyi/nyi))=0
c      f(n+1) - sum(y(i)-x(i))=0
c      f(n+2) - py=px
c      f(n+3) - b/binput-1=0, where b = p, t, d, or s
c
c  variables:
c     1 to nc - log(k(i))
c     nc+1    - log(t)
c     nc+2    - log(p) or log(rhox)
c     nc+3    -           log(rhoy)
c


  subroutine MAXP (x,tm,pm,Dm,ierr,herr)
c
c  values at the maximum pressure along the saturation line, these are
c  returned from the call to SATSPLN and apply only to the composition x
c  sent to SATSPLN.
c
c  input:
c        x--composition [array of mol frac]
c  outputs:
c       tm--temperature [K]
c       pm--pressure [kPa]
c       Dm--density [mol/L]
c     ierr--error flag:  0 = successful
c     herr--error string (character*255 variable if ierr<>0)
c


      subroutine DERVPVT (t,rho,x,
     &                    dPdD,dPdT,d2PdD2,d2PdT2,d2PdTD,
     &                    dDdP,dDdT,d2DdP2,d2DdT2,d2DdPT,
     &                    dTdP,dTdD,d2TdP2,d2TdD2,d2TdPD)
c
c  compute derivatives of temperature, pressure, and density
c  using core functions for Helmholtz free energy equations only
c
c  inputs:
c        t--temperature [K]
c      rho--molar density [mol/L]
c        x--composition [array of mol frac]
c  outputs:
c     dPdD--derivative dP/drho [kPa-L/mol]
c     dPdT--derivative dP/dT [kPa/K]
c     dDdP--derivative drho/dP [mol/(L-kPa)]
c     dDdT--derivative drho/dT [mol/(L-K)]
c     dTdP--derivative dT/dP [K/kPa]
c     dTdD--derivative dT/drho [(L-K)/mol]
c   d2PdD2--derivative d^2P/drho^2 [kPa-L^2/mol^2]
c   d2PdT2--derivative d2P/dT2 [kPa/K^2]
c   d2PdTD--derivative d2P/dTd(rho) [J/mol-K]

  subroutine DBDT2 (t,x,dbt2)
c
c  compute the 2nd derivative of B (B is the second virial coefficient) with
c  respect to T as a function of temperature and composition.
c
c  inputs:
c        t--temperature [K]
c        x--composition [array of mol frac]
c  outputs:
c      dbt2--2nd derivative of B with respect to T [L/mol-K^2]
c

subroutine VIRBCD (t,x,b,c,d)
c
c  Compute virial coefficients as a function of temperature
c  and composition.  The routine currently works only for pure fluids and
c  for the Helmholtz equation.
c  All values are computed exactly based on the terms in the eos, not
c  as done in VIRB by calculating properties at rho=1.d-8.
c
c  inputs:
c        t--temperature [K]
c        x--composition [array of mol frac]
c  outputs:
c        b--second virial coefficient [l/mol]
c        c-- third virial coefficient [(l/mol)^2]
c        d--fourth virial coefficient [(l/mol)^3]
c



      subroutine HEAT (t,rho,x,hg,hn,ierr,herr)
c
c  Compute the ideal gas gross and net heating values.
c
c  inputs:
c        t--temperature [K]
c      rho--molar density [mol/L]
c        x--composition [array of mol frac]
c
c  outputs:
c       hg--gross (or superior) heating value [J/mol]
c       hn--net (or inferior) heating value [J/mol]
c     ierr--error flag:  0 = successful
c                        1 = error in chemical formula
c                        2 = not all heating values available
c     herr--error string (character*255 variable if ierr<>0)
c


"""

if __name__ == u'__main__':
    _test()

    #import profile
    #profile.run('_test()')

