# encoding: utf-8
import re
import json
from workflow import web, Workflow

def get_artwork(podcast_or_episode, cache_directory, size=60):
    '''
    Takes a podcast or episode dictionary (with an artworkUrl100 key)
    and downloads the aassociated image
    '''

    # What are the available artwork sizes?
    # artwork_sizes = [int(key.replace('artworkUrl', ''))
    #                  for key in podcast_or_episode.keys()
    #                  if key.startswith('artworkUrl')]

    artwork_url = podcast_or_episode.get('artworkUrl{}'.format(size), None)
    artwork = web.get(url=artwork_url)
    artwork.raise_for_status()
    
    # This works because both podcasts and episodes have a trackId value
    artwork_path = '{}/{trackId}.jpg'.format(cache_directory, **podcast_or_episode)
    artwork.save_to_path(artwork_path)
    return artwork_path


def main(wf):
    '''
    Retrieves a list of podcasts from the cache, downloads the series-level artwork and saves it to disk,
    then caches the path to this file
    '''

    entities_with_missing_artwork = wf.cached_data('entities_with_missing_artwork', max_age=0)

    for entity in entities_with_missing_artwork:
        # This works because both podcasts and episodes have a trackId value
        wf.logger.warning(entity['trackId'])
        artwork=wf.cached_data(name=entity['trackId'],
                            data_func=lambda: get_artwork(podcast_or_episode=entity, cache_directory=wf.cachedir),
                            max_age=3600)


if __name__ == '__main__':
    wf = Workflow()
    wf.run(main)