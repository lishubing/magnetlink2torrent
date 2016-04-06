import re
from requests import Session
from requests.exceptions import RequestException
from django.http import HttpResponse, FileResponse, HttpResponseRedirect
from django.shortcuts import render
from .form import SearchForm
from .redis_utils import redis


def index(request):
    form = SearchForm()
    return render(request, 'index.html', {'form':form})


def make_torrent_response(content, filename):
    response = FileResponse(content,
                            content_type='application/x-bittorrent')
    response['Content-Disposition'] = \
        'attachment; filename="{0}.torrent"'.format(filename)
    return response


def torrent(request):
    session = Session()
    input_hash = request.GET.get('h')
    if not input_hash:
        return HttpResponse('Bad Request', status=400)
    re_pattern = re.compile(r'\w{40}')
    torrent_hash_list = re.findall(re_pattern, input_hash)
    if torrent_hash_list:
        torrent_hash = torrent_hash_list[0].upper()
    else:
        return HttpResponse('Not Found', status=404)
    torrent_content = redis.get(torrent_hash)

    if torrent_content:
        return make_torrent_response(torrent_content, torrent_hash)

    btbox_url = 'http://bt.box.n0808.com/{0}/{1}/{2}.torrent'.format(
        torrent_hash[:2], torrent_hash[-2:], torrent_hash
    )
    torcache_url = 'http://torcache.net/torrent/{0}.torrent'.format(
        torrent_hash)
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_3) '
                      'AppleWebKit/537.36 (KHTML, like Gecko) '
                      'Chrome/49.0.2623.87 Safari/537.36'})
    print torcache_url, btbox_url
    try:
        session_res = session.get(torcache_url)
        assert session_res.status_code == 200
    except (AssertionError, RequestException):
        try:
            session_res = session.get(btbox_url)
            assert session_res.status_code == 200
        except (AssertionError, RequestException):
            return HttpResponseRedirect('http://www.btcache.me/torrent/' +
                                        torrent_hash)
    redis.set(torrent_hash, session_res.content)
    return make_torrent_response(session_res.content, torrent_hash)
