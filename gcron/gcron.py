#!/usr/bin/python

import os
import sys
import urllib
import re
import datetime
import logging
import ConfigParser
import optparse
import time

import icalendar
import pytz

import rrule

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

class Gcron (object):
    def __init__ (self, cfg):
        self.url = cfg.get('gcron', 'url')
        self.interval = cfg.get('gcron', 'interval')
        self.log = logging.getLogger('gcron')

    def run(self):
        while True:
            loop_start = time.time()

            self.load()
            self.parse()
            print self.data

            time.sleep(float(self.interval) - (time.time() - loop_start))

    def load(self):
        urlfd = urllib.urlopen(self.url)
        text = []
        for line in urlfd:
            if line.startswith('CREATED'):
                continue
            else:
                text.append(line.strip())

        self.ical = icalendar.Calendar.from_string('\n'.join(text))

    def parse(self):
        self.data = {
                'events': [],
                'tz': pytz.utc,
                }
        for component in self.ical.walk():
            if component.name == 'VTIMEZONE' and 'TZID' in component:
                self.data['tz'] = pytz.timezone(component['TZID'])
            elif component.name == 'VEVENT':
                if component.get('DESCRIPTION', '').startswith('#!'):
                    event = { 'description': component['SUMMARY'],
                            'uid': component['UID'],
                            'script': component['DESCRIPTION'],
                            }
                    dtstart = component['DTSTART'].dt
                    if not dtstart.tzinfo:
                        dtstart = self.data['tz'].localize(component['DTSTART'].dt)
                    event['dtstart'] = dtstart.astimezone(self.data['tz'])

                    if 'RRULE' in component:
                        rep = component['RRULE']
                        event['rrule'] = rrule.mkrrule(rep, dtstart=dtstart.replace(tzinfo=None))

                    self.data['events'].append(event)

def parse_args():
    p = optparse.OptionParser()
    p.add_option('-f', '--config-file', default='gcron.ini')
    p.add_option('-i', '--interval')
    return p.parse_args()

def run():
    opts, args = parse_args()
    cfg = ConfigParser.ConfigParser()
    cfg.readfp(open(opts.config_file))

    if opts.interval:
        cfg.set('gcron', 'interval', opts.interval)

    g = Gcron(cfg)
    g.run()

