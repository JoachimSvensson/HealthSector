from app import create_app

flask_app = create_app()


if __name__ == '__main__':
    # app.run(debug=True)
    from werkzeug.serving import run_simple
    run_simple('localhost', 5000, flask_app)