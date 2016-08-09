from flask import Flask
from flask import render_template, make_response, after_this_request
from flask import request
from flask import jsonify
import run_search
import json

app = Flask(__name__)
app.debug = True

@app.route('/')
def index():
	resp = make_response(render_template('index.html'))
	query = request.args.get('query')
	if (query != None):
		results = {}
		search_results = run_search.get_related_works(query)
		for i in range(0, len(search_results)):
			key = str(i)
			results[key] = {}
			results[key]['doc_id'] = str(search_results[i][0])
			results[key]['sim_score'] = str(search_results[i][1])
		# print(type(results))
		resp.headers['search_results'] = json.dumps(results)
	return resp
	

# Requests
# @app.route('/')
# def login():
# 	print("hello world")
# 	print(request.args.get("query"))
#     if request.method == 'POST':
#         do_the_login()
#     else:
#         show_the_login_form()