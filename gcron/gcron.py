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
import cStringIO as StringIO

import vobject
import pytz

import rrule
import script

class Gcron (object):
    def __init__ (self, cfg):
        self.url = cfg.get('gcron', 'url')
        self.interval = cfg.get('gcron', 'interval')
        self.log = logging.getLogger('gcron')
        self.log.addHandler(logging.StreamHandler())
        self.log.setLevel(logging.INFO)
        self.delta = datetime.timedelta(seconds=int(cfg.get('gcron', 'delta')))

    def run(self):
        self.log.info('Starting up.')
        while True:
            loop_start = time.time()

            self.load()
            self.parse()
            self.execute()

            time.sleep(float(self.interval) - (time.time() - loop_start))

    def load(self):
        textfd = StringIO.StringIO()
        self.log.info('Loading calendar from %s.' % self.url)
        urlfd = urllib.urlopen(self.url)
        for line in urlfd:
            if not line.startswith('CREATED'):
                textfd.write(line)
        textfd.seek(0)

        self.log.info('Parsing calendar.')
        self.ical = vobject.readOne(textfd)

    def parse(self):
        self.events = []
        self.log.info('Processing calendar components.')
        for component in self.ical.getChildren():
            if component.name == 'VTIMEZONE':
                self.tz = component.tzinfo
            elif component.name == 'VEVENT':
                event = {
                        'description': component.summary.value,
                        'uid': component.uid.value,
                        'script': component.description.value,
                        'dtstart': component.dtstart.value,
                        'rruleset': component.getrruleset(),
                        }
                self.log.info('Added event "%(description)s" (uid %(uid)s).' % event)

                self.events.append(event)

    def execute(self):
        now = datetime.datetime.now(pytz.utc)

        for event in self.events:
            print event
            print 'now:', now
            print 'start:', event['dtstart']
            if now > event['dtstart']:
                self.log.info('Skipping event %(uid)s: in the past.' % event)
                continue

            if event['rruleset']:
                next = event['rruleset'].after(now)
            else:
                next = event['dtstart']

            delta = next - now
            if delta <= self.delta:
                print 'Execute now!'

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

