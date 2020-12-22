# encoding: utf-8
import re
import json
from urllib import unquote
from workflow import web, Workflow
import argparse


def token_still_valid(bearer_token):
    '''Perform a test call to the AMP API  endpoint to determine whether our bearer token is still valid'''

    if not bearer_token:
        wf.logger.warning('Looks like an empty bearer token')
        return False

    try:
        r = web.get(
            url="https://amp-api.podcasts.apple.com/v1/catalog/us/podcasts/201671138", # TAL
            headers={
                "Authorization": "Bearer {}".format(bearer_token),
            })
        r.raise_for_status()
        return True

    except Exception as e:
        wf.logger.warning('Looks like the bearer token is not valid! {}'.format(e))
        return False


def get_bearer_token():
    '''
    Visits the Apple Podcasts preview for a known podcast (This American Life) to retrieve
    a bearer token we can use for AMP API requests.
    '''

    pattern = r"""<meta name=\"web-experience-app/config/environment\" content=\"(.+?)\" />"""

    r = web.get(
        'https://podcasts.apple.com/us/podcast/this-american-life/id201671138')
    r.raise_for_status()

    match = re.search(pattern, r.content)
    match_unquoted = unquote(match.group(1))
    environment = json.loads(match_unquoted)

    wf.logger.info(environment.get('MEDIA_API').get('token').strip())
    return environment.get('MEDIA_API').get('token').strip()

def main(wf):
    ''' Retrieve bearer token from cache and proactively check it it still works'''

    # Fetch the (possibly stale) bearer token from the cache
    cached_bearer_token = wf.cached_data('apple_amp_api_bearer_token', max_age=0)

    wf.logger.info("The (possibly stale) cached bearer token is {}".format(cached_bearer_token))

    if token_still_valid(cached_bearer_token):
        wf.logger.info("Cached bearer token is still valid")
    else:
        wf.logger.warning("Stale bearer token {}".format(cached_bearer_token))
        
        # fetch a new bearer token and store it in the cache
        fresh_bearer_token = get_bearer_token()
        wf.cache_data('apple_amp_api_bearer_token', fresh_bearer_token)
        wf.logger.info("Fetched and stored fresh bearer token {}".format(fresh_bearer_token))

if __name__ == '__main__':
    wf = Workflow()
    wf.run(main)