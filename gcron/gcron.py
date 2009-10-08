#!/usr/bin/python

import os
import sys
import urllib
import datetime
import logging
import ConfigParser
import optparse
import time
import pprint

import icalendar
import pytz

import rrule

class Gcron (object):
    def __init__ (self, cfg):
        self.url = cfg.get('gcron', 'url')
        self.interval = cfg.get('gcron', 'interval')
        self.log = logging.getLogger('gcron')
        self.delta = datetime.timedelta(seconds=int(cfg.get('gcron', 'delta')))

    def run(self):
        while True:
            loop_start = time.time()

            self.load()
            self.parse()
            pprint.pprint( self.events)

            self.execute()

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
        self.events = []
        for component in self.ical.walk():
            if component.name == 'VTIMEZONE' and 'TZID' in component:
                self.tz = pytz.timezone(component['TZID'])
            elif component.name == 'VEVENT':
                if component.get('DESCRIPTION', '').startswith('#!'):
                    event = { 'description': component['SUMMARY'],
                            'uid': component['UID'],
                            'script': component['DESCRIPTION'],
                            }
                    dtstart = component['DTSTART'].dt
                    if not dtstart.tzinfo:
                        dtstart = self.tz.localize(component['DTSTART'].dt)
                    event['dtstart'] = dtstart.astimezone(self.tz)

                    if 'RRULE' in component:
                        rep = component['RRULE']
                        event['rrule'] = rrule.mkrrule(rep, dtstart=dtstart.replace(tzinfo=None))

                    self.events.append(event)

    def execute(self):
        now = datetime.datetime.today()

        for event in self.events:
            if 'rrule' in event:
                next = event['rrule'].after(now, True)
            else:
                next = event['dtstart']

            try:
                delta = next - now
            except TypeError:
                delta = next - self.tz.localize(now)

            print 'Event %s next due at %s.' % (event['uid'], next)
            print 'Event Delta:',  delta
            print 'Max delta:', self.delta

            if delta <= self.delta:
                print 'Execute now!'
                print event['script']
                print

            print

def parse_args():
    p = optparse.OptionParser()
    p.add_option('-f', '--config-file', default='gcron.ini')
    p.add_option('-i', '--interval')
    p.add_option('-d', '--delta')
    return p.parse_args()

def run():
    opts, args = parse_args()
    cfg = ConfigParser.ConfigParser()
    cfg.readfp(open(opts.config_file))

    if opts.interval:
        cfg.set('gcron', 'interval', opts.interval)

    if opts.delta:
        cfg.set('gcron', 'delta', opts.delta)

    g = Gcron(cfg)
    g.run()

