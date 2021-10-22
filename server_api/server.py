import os

from flask import Flask, jsonify, abort, make_response, request, render_template
import requests
import json
import time
import sys
import pandas as pd
from prediction import SocialRecommend
import logging
logging.basicConfig(filename='logs/logs.log',level=logging.DEBUG)

app = Flask(__name__)

recommender = SocialRecommend()


def launch_task(take_info_migration, api):
    print(take_info_migration, api)
    pred_recomend = recommender.predict(take_info_migration)
    if api == 'v1.0':
        res_dict = pred_recomend
        return res_dict
    else:
        res_dict = {'error': 'API doesnt exist'}
        return res_dict


@app.route('/social/api/v1.0/getpred', methods=['GET'])
def get_task():
    try:
        result = launch_task(request.args.get('take_into_migration'), 'v1.0')
        logging.info('Информационное сообщение')
        return make_response(jsonify(result), 200)
    except:
        logging.debug('Ошибка')

@app.route('/render_map')
def render_the_map():
    return render_template(r'map.html')

@app.errorhandler(404)
def not_found(error):
    logging.warning('Предупреждение')
    return make_response(jsonify({'code': 'PAGE_NOT_FOUND'}), 404)

@app.errorhandler(500)
def server_error(error):
    logging.warning('Предупреждение')
    return make_response(jsonify({'code': 'INTERNAL_SERVER_ERROR'}), 500)

if __name__ == '__main__':
    app.run(port=5000, debug=True)