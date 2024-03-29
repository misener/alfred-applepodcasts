#!/usr/bin/python
# encoding: utf-8

import re
import sys
import json
import base64
from urllib import unquote
from workflow import Workflow3, ICON_WEB, ICON_INFO, web
from update_opawg_data import get_opawg_data
import base64
from workflow.background import run_in_background, is_running, kill


def string_boolean_to_emoji(string):
    return'✅' if bool(int(string)) else "❌"


def main(wf):

    podcast = json.loads(wf.args[0])

    series = wf.add_item(title=podcast['collectionName'],
                         subtitle="Open in Apple Podcasts (or hit a modifier key for additional platforms)",
                         icon='icon.png',
                         valid=True,
                         arg=(podcast['collectionViewUrl']
                              .replace('?uo=4', '')
                              if podcast['collectionViewUrl']
                              .endswith('?uo=4')
                              else podcast['collectionViewUrl'])
                         )

    # TODO: add website as an option: move episode fetch earlier, and use the [0]['websiteUrl'] value

    series.add_modifier(key='ctrl',
                        subtitle=u'Open {collectionName} in PodLink'.format(
                            **podcast),
                        icon='icons/podlink.jpg',
                        arg=u"https://pod.link/{collectionId}".format(
                            **podcast),
                        valid=True)

    series.add_modifier(key='cmd',
                        subtitle='Open in Podchaser',
                        icon='icons/podchaser.png',
                        arg="https://www.podchaser.com/f/pod/{}".format(
                            podcast['collectionId']),
                        valid=True)

    if 'feedUrl' in podcast:
        series.add_modifier(key='alt',
                            subtitle='Open in Google Podcasts',
                            icon='icons/google.png',
                            arg="https://podcasts.google.com/feed/{}".format(
                                base64.urlsafe_b64encode(
                                    podcast['feedUrl'].encode("utf-8"))
                            ),
                            valid=True)

        wf.add_item(title="RSS",
                    subtitle=podcast['feedUrl'],
                    copytext=podcast['feedUrl'],
                    valid=True,
                    arg=podcast['feedUrl'],
                    icon='icons/rss.png')

    artwork_url = podcast['artworkUrl600'].replace('600x600', "3000x3000")

    wf.add_item(title="Series artwork",
                subtitle=artwork_url,
                valid=True,
                arg=artwork_url,
                copytext=artwork_url,
                icon=ICON_WEB,
                )

    series_metadata = wf.add_item(title="Apple Podcasts ID",
                                  subtitle="Podcast ID: {collectionId}".format(
                                      **podcast),
                                  copytext=podcast['collectionId'],
                                  icon=ICON_INFO,
                                  )

    if 'artistId' in podcast:
        series_metadata.add_modifier(key='cmd',
                                     subtitle='Artist ID: {artistId}'.format(
                                         **podcast),
                                     arg=podcast['artistViewUrl'],
                                     valid=True)

    wf.cache_data('podcast_to_lookup_episodes', podcast)

    # Is episode cache over 5 minutes old or non-existent?
    if not wf.cached_data_fresh("{}_episodes_metadata".format(podcast['collectionId']), 300):
        run_in_background('update_podcast_episodes',
                          ['/usr/bin/python',
                           wf.workflowfile('update_podcast_episodes.py')])

    if is_running('update_podcast_episodes'):
        wf.rerun = 0.5
        wf.add_item('Fetching episodes...',
                    valid=False,
                    )

    episodes = wf.cached_data(name="{}_episodes_metadata".format(
        podcast['collectionId'], max_age=0))

    if episodes:
        # OPAWG host data
        # No worry about max age because we were proactive in main.py
        hosts_json = wf.cached_data(name='opawg_hosts', max_age=0)

        host = next((host for host in hosts_json
                     if host['regex'].search(episodes[0]['episodeUrl'])), None)

        if host:
            wf.add_item(title="Audio hosted by {hostname}".format(**host),
                        subtitle=" / ".join(["{} {}".format(
                            string_boolean_to_emoji(
                                v), k.replace('abilities_', '').title()
                        )
                            for k, v in host.items()
                            if k.startswith('abilities_')]),
                        icon=ICON_INFO,
                        arg=host['hosturl'],
                        valid=True
                        )

        # OPAWG prefix data
        # No worry about max age because we were proactive in main.py
        prefixes_json = wf.cached_data(name='opawg_prefixes', max_age=0)

        wf.logger.warning(episodes[0])

        installed_prefixes = [prefix for prefix
                              in prefixes_json
                              if prefix['regex'].search(episodes[0]['episodeUrl'])]

        if len(installed_prefixes) > 0:
            prefix_names = [prefix['prefixname']
                            for prefix
                            in installed_prefixes]

            wf.add_item(title="Prefixes: {}".format(", ".join(prefix_names)),
                        icon=ICON_INFO)

    if episodes:
        for episode in episodes:
            item = wf.add_item(title=episode['trackName'],
                               subtitle=episode['episodeUrl'],
                               #    uid=episode['attributes']['guid'],
                               arg=episode['episodeUrl'],
                               icon=ICON_WEB,
                               valid=True,
                               )

            item.add_modifier(key='cmd',
                              subtitle='View episode in Apple Podcasts',
                              arg=episode['trackViewUrl'],
                              icon='icon.png',
                              valid=True)

    wf.send_feedback()


if __name__ == '__main__':
    wf = Workflow3()
    log = wf.logger
    sys.exit(wf.run(main))
