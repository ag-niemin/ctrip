import ocr
import json
import tornado.web
import tornado.ioloop
from tornado.options import define, options

define('port', default=1234, help='运行端口', type=int)


class MainHandler(tornado.web.RequestHandler):
    def get(self):
        self.render('index.html')


class OcrHandler(tornado.web.RequestHandler):
    def post(self):
        files = self.request.files['files']
        for file in files:
            filename = file['filename']
            img = file['body']
            result = ocr.result(img)
            result = json.dumps(result, ensure_ascii=False)
            print(result)
            self.write('<p>{}: {}</p>'.format(filename, result))
        self.flush()


if __name__ == '__main__':
    settings = {
        'template_path': 'templates',
    }
    app = tornado.web.Application(
        [
            (r'/', MainHandler),
            (r'/ocr', OcrHandler),
        ], **settings)
    app.listen(options.port)
    print('http://localhost:{}/'.format(options.port))
    tornado.ioloop.IOLoop.current().start()
