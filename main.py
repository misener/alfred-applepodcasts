#!/usr/bin/python
# encoding: utf-8

import timeago
from datetime import datetime
import sys
import json
from workflow import Workflow3, web
from workflow.background import run_in_background, is_running

def search(query):
    podcasts = web.get(url='https://itunes.apple.com/search',
                       params={'media': 'podcast',
                               'term': query})
    podcasts.raise_for_status()
    return podcasts.json()['results']  

def main(wf):
    query = wf.args[0]
    
    # Cache the results of our search for 1 minute so wf.rerun doesn't keep hitting the API
    podcasts = wf.cached_data(name=query, data_func=lambda: search(query), max_age=60)

    for podcast in podcasts:
        datetime_object = datetime.strptime(
            podcast['releaseDate'], '%Y-%m-%dT%H:%M:%SZ')

        podcast['time_ago'] = timeago.format(
            datetime_object, datetime.now())

        wf.add_item(title=podcast['collectionName'],
                    subtitle=u"{artistName} / {primaryGenreName} / {trackCount} episodes / Updated {time_ago}".format(
                        **podcast),
                    arg=json.dumps(podcast), # TODO: instead of dumping JSON here, could we write it to the cache and pick it up in the podcast.py script?
                    quicklookurl=podcast.get('artworkUrl600', None),
                    uid=podcast.get('collectionId', None),
                    copytext=podcast.get('collectionName', None),
                    icon=wf.cached_data(name=podcast['trackId'],
                                        max_age=3600),
                    valid=True,
                    )

    # Get fresh OPAWG data
    if not wf.cached_data_fresh('opawg_hosts', max_age=86400):
        run_in_background('update_opawg_data', ['/usr/bin/python', wf.workflowfile('update_opawg_data.py')])

    # Update series-level artwork in the background
    podcasts_with_missing_artwork = [podcast for podcast in podcasts if not wf.cached_data_fresh(podcast['trackId'], 3600)]    
    wf.cache_data('entities_with_missing_artwork', podcasts_with_missing_artwork)

    if len(podcasts_with_missing_artwork) > 0:
        run_in_background('update_artwork',
                ['/usr/bin/python',
                wf.workflowfile('update_artwork.py')])

    if is_running('update_artwork'):
        wf.rerun = 0.5
        wf.add_item('Fetching artwork...', valid=False)

    wf.send_feedback()


if __name__ == '__main__':
    wf = Workflow3()
    sys.exit(wf.run(main))
