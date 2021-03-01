# encoding: utf-8
import re
import json
from urllib import unquote
from workflow import web, Workflow


def get_opawg_data(source='hosts'):
    '''
    Given the string 'hosts' or 'prefixes', fetches the lastest JSON data
    from https://github.com/opawg then generate compiled regexes for:

    prefixes: prefixpattern
    hosts: pattern
    '''

    d = {'hosts': {'github_slug': 'hosts',
                   'pattern_key': 'pattern'},
         'prefixes': {'github_slug': 'prefixes',
                      'pattern_key': 'prefixpattern'}}

    opawg_data = web.get(
        'https://raw.githubusercontent.com/opawg/podcast-{github_slug}/master/src/{github_slug}.json'.format(**d[source])).json()

    for entry in opawg_data:
        entry['regex'] = re.compile(
            entry.get(d[source]['pattern_key']), re.IGNORECASE)

    return opawg_data


def main(wf):
    ''' Proactively fetch fresh OPAWG data if it's more than 1 day old '''
    
    for data_source in ['hosts', 'prefixes']:
        x = wf.cached_data(name='opawg_{}'.format(data_source),
                                data_func=lambda: get_opawg_data(data_source),
                                max_age=86400)

if __name__ == '__main__':
    wf = Workflow()
    wf.run(main)