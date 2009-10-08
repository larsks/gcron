#!/usr/bin/python

import os
import sys
import urllib
import re
import datetime
import logging

import icalendar
import dateutil.rrule as rrule
import dateutil.parser as parser
import pytz

re_named_period = re.compile('(\d*)(\w+)')

def parse_named_period (wd):
    mo = re_named_period.match(wd)
    c = getattr(rrule, mo.group(2))

    if mo.group(1):
        return c(int(mo.group(1)))
    else:
        return c

fieldmap = {
        'FREQ':     ('freq',        lambda(x): getattr(rrule, x)),
        'BYDAY':    ('byweekday',   parse_named_period),
        'BYMONTH':  ('bymonth',     int),
        'WKST':     ('wkst',        lambda(x): getattr(rrule, x)),
        'INTERVAL': ('interval',    int),
        'UNTIL':    ('until',       lambda x: tz.fromutc(x).replace(tzinfo=None)),
        }

cal = icalendar.Calendar.from_string(open('calendar.ical').read())
now = datetime.datetime.today()

def mkrrule(r, **kwargs):
    ruledict = {}

    for k,v in kwargs.items():
        if k is not None:
            ruledict[k] = v

    for k,v in r.items():
        if k in fieldmap:
            if fieldmap[k][1] is None:
                continue
            else:
                ruledict[fieldmap[k][0]] = fieldmap[k][1](v[0])
        else:
            ruledict[k.lower()] = str(v[0])

    print 'ruledict:', ruledict

    return rrule.rrule(**ruledict)


class Gcron (object):
    def __init__ (self, url=None, interval=1800):
        self.url = url
        self.interval = interval
        self.log = logging.getLogger('gcron')

    def run(self):
        while True:
            loop_start = time.time()

            urlfd = urllib.openurl(self.url)
            cal = icalendar.Calendar.from_string(urlfd.read())
        
            self.parse(cal)

            time.sleep(self.interval - (time.time() - loop_start))

    def parse(self, cal):
        cald = {}
        for component in cal.walk():
            if component.name == 'VTIMEZONE' and 'TZID' in component:
                cald{'tz'} = pytz.timezone(component['TZID'])
            elif component.name == 'VEVENT':
                if component.get('DESCRIPTION', '').startswith('#!'):
                    print 'Found an executable item.'
                    print '  Description:', component['SUMMARY']
                    print '  UID:', component['UID']
                    t_start = component['DTSTART'].dt

                    if not t_start.tzinfo:
                        t_start = tz.localize(component['DTSTART'].dt)

                    t_start = t_start.astimezone(tz)

                    print '  Starts:', t_start

                    if 'RRULE' in component:
                        rep = component['RRULE']
                        print rep
                        print 'Repeats %s.' % rep['FREQ'][0]

                        rule = mkrrule(rep, dtstart=t_start.replace(tzinfo=None))
                        t_run = rule.after(datetime.datetime.now())
                    else:
                        t_run = t_start

                    print 'next executes:', t_run
                    print

def parse_args():
    p = optparse.OptionParser()
    p.add_option('-f', '--feed-url')
    p.add_option('-i', '--interval')
    return p.parse_args()

def run():
    opts, args = parse_args()
    g = Gcron(url=opts.feed_url, interval=opts.interval)
    g.run()


