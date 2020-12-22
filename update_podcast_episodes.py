# encoding: utf-8
import re
import json
from workflow import web, Workflow

def lookup_episodes(podcast):
    lookup = web.get(
        url="https://itunes.apple.com/lookup",
        params={"id": podcast.get('trackId'),
                "entity": "podcastEpisode",
                "limit": "3"}) # make this user-configurable?

    lookup.raise_for_status()
    lookup_results = lookup.json()['results']
    
    podcasts = [result for result in lookup_results if result['kind'] == 'podcast']
    episodes = [result for result in lookup_results if result['kind'] == 'podcast-episode']
    
    return episodes


def main(wf):
    '''
    Retrieves a list of podcasts from the cache, downloads the series-level artwork and saves it to disk,
    then caches the path to this file
    '''

    podcast = wf.cached_data('podcast_to_lookup_episodes', max_age=0)

    podcast_episodes = wf.cached_data(name="{}_episodes_metadata".format(podcast['collectionId']),
                        data_func=lambda: lookup_episodes(podcast),
                        max_age=300)


if __name__ == '__main__':
    wf = Workflow()
    wf.run(main)