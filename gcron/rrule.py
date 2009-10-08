import re
import dateutil.rrule

re_named_period = re.compile('(\d*)(\w+)')

def get_rrule_constant (x):
    return getattr(dateutil.rrule, x)

def parse_named_period (wd):
    mo = re_named_period.match(wd)
    if not mo:
        raise ValueError(wd)

    c= get_rrule_constant(mo.group(2))

    if mo.group(1):
        return c(int(mo.group(1)))
    else:
        return c

# XXX: This is broken!  xform function for UNTIL references unbound
# variable tz.  This used to be global, but now it is only defined 
# in the context of a Gcron() object.  What to do?
fieldmap = {
        'FREQ':     { 'xform': get_rrule_constant },
        'BYDAY':    { 'name': 'byweekday',
            'xform': parse_named_period },
        'BYMONTH':  { 'xform': int },
        'WKST':     { 'xform': get_rrule_constant },
        'INTERVAL': { 'xform': int },
        'UNTIL':    { 'xform': lambda x:
            tz.fromutc(x).replace(tzinfo=None)},
        }

def mkrrule(r, **kwargs):
    ruledict = {}
    ruledict.update(kwargs)

    for k,v in r.items():
        if k in fieldmap:
            if fieldmap[k].get('ignore'):
                continue
            else:
                ruledict[fieldmap[k].get('name', k.lower())] \
                        = fieldmap[k].get('xform', str)(v[0])
        else:
            ruledict[k.lower()] = str(v[0])

    return dateutil.rrule.rrule(**ruledict)

