#!/usr/bin/python
# encoding: utf-8

import timeago
from datetime import datetime
import sys
import json
from workflow import Workflow3, web, ICON_INFO
from workflow.background import run_in_background, is_running


def search(query):
    podcasts = web.get(url='https://itunes.apple.com/search',
                       params={'media': 'podcast',
                               'term': query})
    podcasts.raise_for_status()
    return podcasts.json().get('results')


def main(wf):
    query = wf.args[0]

    if wf.update_available:
        # Add a notification to top of Script Filter results
        wf.add_item('New version available',
                    'Action this item to install the update',
                    autocomplete='workflow:update',
                    icon=ICON_INFO)

    # Cache the results of our search for 1 minute so wf.rerun doesn't keep hitting the API
    podcasts = wf.cached_data(name=query,
                              data_func=lambda: search(query), max_age=60)

    for podcast in podcasts:
        datetime_object = datetime.strptime(
            podcast['releaseDate'], '%Y-%m-%dT%H:%M:%SZ')

        podcast['time_ago'] = timeago.format(
            datetime_object, datetime.now())

        wf.add_item(title=podcast['collectionName'],
                    subtitle=u"{artistName} / {primaryGenreName} / {trackCount} episodes / Updated {time_ago}".format(
                        **podcast),
                    # TODO: instead of dumping JSON here, could we write it to the cache and pick it up in the podcast.py script?
                    arg=json.dumps(podcast),
                    quicklookurl=podcast.get('artworkUrl600', None),
                    uid=podcast.get('collectionId', None),
                    copytext=podcast.get('collectionName', None),
                    icon='icon.png',
                    valid=True,
                    )

    # Get fresh OPAWG data
    if not wf.cached_data_fresh('opawg_hosts', max_age=86400):
        run_in_background('update_opawg_data', [
                          '/usr/bin/python', wf.workflowfile('update_opawg_data.py')])

    wf.send_feedback()


if __name__ == '__main__':
    wf = Workflow3(update_settings={
                   'github_slug': 'misener/alfred-applepodcasts'})
    sys.exit(wf.run(main))
