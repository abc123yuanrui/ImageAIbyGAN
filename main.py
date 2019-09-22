from flask import Flask, jsonify, request
#import sys
#sys.path.append('/home/ryuan/ImageAI/ImageMaster')
from flask_cors import CORS, cross_origin
from ImageMaster import GANProcessor

app = Flask(__name__)
CORS(app)
app.config['CORS_HEADERS'] = 'Content-Type'


@app.route("/")
def hello():
    return "Hello RuiYuan!"

@app.route("/ImgProcess", methods=['GET', 'POST'])
@cross_origin()
def sage_img():
    jsonData = request.get_json()
    if not jsonData:
        return jsonify({'error': 'No data provided.'}), 400
    imgListin = jsonData.get('imgList')
    if not imgListin:
        return jsonify({'error': 'No image provided.'}), 400
    imgListout = GANProcessor(imgListin);
    print('DATA PROCESSED SUCCESSFULLY!!!!')
    res={}
    res['processed_imgList']=[str(i) for i in imgListout]
    return jsonify(res)

if __name__ == "__main__":
    # Only for debugging while developing
    app.run(host='0.0.0.0', debug=True, port=80)
