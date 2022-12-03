from app import app
from app import src_api as film
from flask import request, jsonify, abort
@app.route('/')
@app.route('/index')
def index():
    return "hello"
    

@app.route('/search', methods=['GET'])
def paginate():
    q = request.args.get('q')
    movie = film.search(q)
    print(len(movie))
    #return movie
    
    return jsonify(get_paginated_list(
		movie, 
		'/search', 
		start=request.args.get('start', 1), 
		limit=request.args.get('limit', 20)
	  ))
	  
	
	
@app.route('/show', methods=['GET'])
def show():
    args = request.args.get('id')
    return film.show(args)

@app.route('/download', methods=['GET'])
def download():
    args = request.args.get('id')
    return film.download(args)





def get_paginated_list(results, url, start, limit):
    start = int(start)
    limit = int(limit)
    count = len(results)
    if count < start or limit < 0:
        abort(404)
    # make response
    obj = {}
    obj['start'] = start
    obj['limit'] = limit
    obj['count'] = count
    # make URLs
    # make previous url
    if start == 1:
        obj['previous'] = ''
    else:
        start_copy = max(1, start - limit)
        limit_copy = start - 1
        obj['previous'] = url + '?start=%d&limit=%d' % (start_copy, limit_copy)
    # make next url
    if start + limit > count:
        obj['next'] = ''
    else:
        start_copy = start + limit
        obj['next'] = url + '?start=%d&limit=%d' % (start_copy, limit)
    # finally extract result according to bounds
    obj['results'] = results[(start - 1):(start - 1 + limit)]
    return obj