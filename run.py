from app import create_app

flask_app = create_app()


if __name__ == '__main__':
    # app.run(debug=True)
    from werkzeug.serving import run_simple
    run_simple('0.0.0.0', 5000, flask_app)