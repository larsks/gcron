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

config_defaults = {
        'run-interval'      : '1800',
        'refresh-interval'  : '10800',
        'debug'             : '0',
        }

class Gcron (object):
    def __init__ (self, cfg):
        self.url = cfg.get('gcron', 'url')
        self.refresh_interval = int(cfg.get('gcron', 'refresh-interval'))
        self.run_interval = int(cfg.get('gcron', 'run-interval'))
        self.last_refresh = 0
        self.events = {}

        self.log = logging.getLogger('gcron')
        self.log.addHandler(logging.StreamHandler())

        if int(cfg.get('gcron', 'debug')):
            self.log.setLevel(logging.DEBUG)
        else:
            self.log.setLevel(logging.INFO)

    def run(self):
        self.log.info('Starting up.')
        while True:
            loop_start = time.time()

            if (loop_start - self.last_refresh) > self.refresh_interval:
                self.log.info('Refresh.')
                self.load()
                self.parse()
                self.last_refresh = loop_start

            self.execute()

            time.sleep(float(self.run_interval) - (time.time() - loop_start))

    def load(self):
        self.tz = pytz.utc

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

                self.events[event['uid']] = event

                self.log.debug('Added event "%(description)s" (uid %(uid)s).' % event)
        self.log.info('Found %d events.' % len(self.events))

    def execute(self):
        now = datetime.datetime.now(pytz.utc).replace(second=0,
                microsecond=0)
        self.log.debug('Now: %s' % now)

        for event in self.events.values():
            if now > event['dtstart']:
                self.log.debug('Removing event %(uid)s: in the past.' % event)
                del self.events[event['uid']]
                continue

            if event['rruleset']:
                next = event['rruleset'].after(now)
            else:
                next = event['dtstart']

            if next == now:
                self.log.info('Execute %(description)s.' % event)
                s = script.Script(text=event['script'])
                res = s.run()
                self.log.info('%s return code: %d' % (event['description'],
                    res))
            else:
                delta = next - now
                self.log.debug('Event %s next executes: %s (delta: %s)' \
                        % (event['description'], next, delta))


def parse_args():
    p = optparse.OptionParser()
    p.add_option('-f', '--config-file', default='gcron.ini')
    p.add_option('--debug', action='store_true')
    p.add_option('-o', '--option', action='append', default=[])
    return p.parse_args()

def run():
    opts, args = parse_args()
    cfg = ConfigParser.ConfigParser(defaults=config_defaults)
    cfg.readfp(open(opts.config_file))

    for cfgopt in opts.option:
        optname, optval = cfgopt.split('=')
        cfg.set('gcron', optname, optval)

    if opts.debug:
        cfg.set('gcron', 'debug', '1')
        print ', '.join(['%s=%s' % (x,y) for (x,y) in
            [(x, cfg.get('gcron', x)) for x in cfg.options('gcron')]])

    g = Gcron(cfg)
    g.run()

