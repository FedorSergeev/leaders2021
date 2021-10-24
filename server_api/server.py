import logging
import sys

from flask import Flask, jsonify, make_response, request, render_template
from flask_cors import CORS, cross_origin

from prediction import SocialRecommend

logging.basicConfig(filename='logs/logs.log', level=logging.DEBUG)
logging.getLogger().addHandler(logging.StreamHandler(sys.stdout))

app = Flask(__name__)
cors = CORS(app)
app.config['CORS_HEADERS'] = 'Content-Type'

social_recommend = SocialRecommend()


def launch_task(new_data_cell: dict):
    logging.info(f"Launch task with params: data='{new_data_cell}'")
    res_dict = social_recommend.predict(new_data_cell)
    return res_dict


@cross_origin()
@app.route('/social/api/v1.0/getpred', methods=['GET', 'POST'])
def get_task():
    new_data_cell = request.json or {}
    logging.info(f'Prediction requested with params: {new_data_cell}')
    result = launch_task(new_data_cell)
    return make_response(jsonify(result), 200)


@cross_origin()
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
    app.run(host="0.0.0.0", port=5000, debug=True)
