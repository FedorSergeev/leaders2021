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


def launch_task(take_info_migration, api):
    logging.info(f"Launch task with params: take_info_migration='{take_info_migration}' and api='{api}'")
    if api == 'v1.0':
        res_dict = social_recommend.predict(take_info_migration)
        return res_dict
    else:
        res_dict = {'error': 'API doesnt exist'}
        return res_dict


@cross_origin()
@app.route('/social/api/v1.0/getpred', methods=['GET'])
def get_task():
    args = request.args
    logging.info(f'Prediction requested with params: {args.to_dict()}')
    take_info_migration = args.get('take_into_migration', '0')
    result = launch_task(take_info_migration, 'v1.0')
    return make_response(jsonify(result), 200)


@cross_origin()
@app.route('/render_map')
def render_the_map():
    return render_template(r'map.html')

@cross_origin()
@app.route('/saveCellValue.js')
def save_cell_value():
    return """
    function saveCellData() {
  console.log("hi");
}
    """


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
