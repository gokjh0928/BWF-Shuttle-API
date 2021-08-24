from flask import Flask
from config import Config
from flask_caching import Cache

cache = Cache(config={'CACHE_TYPE': 'SimpleCache'})

def create_app(config_class=Config):
    # __name__ as reference to current file
    app = Flask(__name__)

    # (configurations, blueprints, additional packages, etc)
    app.config.from_object(config_class)
    cache.init_app(app)

    # tells flask to use this app instance, and use its context
    with app.app_context():
        # now build the rest of the application now that app has been instantiated
        from app.blueprints.main import bp as main
        app.register_blueprint(main)
        from app.blueprints.authentication import bp as authentication
        app.register_blueprint(authentication)
        from app.blueprints.rankings import bp as rankings
        app.register_blueprint(rankings)
        # build routes(paths) ---> Not needed anymore since each blueprint has own route file
        # Create the tables in the database if not exists
        # db.create_all()
    return app