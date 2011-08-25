#!/usr/bin/python
import logging
import os
import cgi
import sys
import urllib

jinja2 = None

_LOCAL_ = os.environ[ 'SERVER_SOFTWARE' ].startswith( 'Development' )
_DEBUG_ = True
_CACHE_ = False

from google.appengine.api import urlfetch
from google.appengine.ext import webapp
from versioned_memcache import memcache

import gist_it
from gist_it import take_slice

def render_gist_html( base, gist, document ):
    if jinja2 is None:
        return
    result = jinja2.get_template( 'gist.jinja.html' ).render( cgi = cgi, base = base, gist = gist, document = document )
    return result

def render_gist_js( base, gist, gist_html  ):
    if jinja2 is None:
        return
    result = jinja2.get_template( 'gist.jinja.js' ).render( base = base, gist = gist, gist_html = gist_html )
    return result

def render_gist_js_callback( callback, gist, gist_html  ):
    return "%s( '%s', '%s' );" % ( callback, gist_html.encode( 'string_escape' ), gist.raw_path )

# dispatch == RequestHandler
def dispatch_gist_it( dispatch, location ):
        base = dispatch.url_for()
        location = urllib.unquote( location )
        match = gist_it.Gist.match( location )
        dispatch.response.headers['Content-Type'] = 'text/plain'; 
        if not match:
            dispatch.response.set_status( 404 )
            dispatch.response.out.write( dispatch.response.http_status_message( 404 ) )
            dispatch.response.out.write( "\n" )
            return

        else:
            gist = gist_it.Gist.parse( location, slice_ = dispatch.request.get( 'slice' ) )
            if not gist:
                dispatch.response.set_status( 500 )
                dispatch.response.out.write( "Unable to parse \"%s\": Not a valid repository path?" % ( location ) )
                dispatch.response.out.write( "\n" )
                return
                
            if _CACHE_ and dispatch.request.get( 'flush' ):
                dispatch.response.out.write( memcache.delete( memcache_key ) )
                return

            memcache_key = gist.raw_url
            data = memcache.get( memcache_key )
            if data is None or not _CACHE_:
                # For below, see: http://stackoverflow.com/questions/2826238/does-google-appengine-cache-external-requests
                response = urlfetch.fetch( gist.raw_url, headers = { 'Cache-Control': 'max-age=300' } )
                if response.status_code != 200:
                    if response.status_code == 403:
                        dispatch.response.set_status( response.status_code )
                    elif response.status_code == 404:
                        dispatch.response.set_status( response.status_code )
                    else:
                        dispatch.response.set_status( 500 )
                    dispatch.response.out.write( "Unable to fetch \"%s\": (%i)" % ( gist.raw_url, response.status_code ) )
                    return
                else:
                    gist_content = take_slice( response.content, gist.start_line, gist.end_line )
                    if dispatch.request.get( 'test' ):
                        dispatch.response.headers['Content-Type'] = 'text/plain'; 
                        dispatch.response.out.write( gist_content )
                        return
                    gist_html = str( render_gist_html( base, gist, gist_content ) ).strip()
                    callback = dispatch.request.get( 'callback' );
                    if callback != '':
                        result = render_gist_js_callback( callback, gist, gist_html )
                    else:
                        result = render_gist_js( base, gist, gist_html )
                    result = str( result ).strip()
                    data = result
                    if _CACHE_:
                        memcache.add( memcache_key, data, 60 * 60 * 24 )

            dispatch.response.headers['Content-Type'] = 'text/javascript'; 
            dispatch.response.out.write( data )
