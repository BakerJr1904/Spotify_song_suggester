from .app import create_app

# telling flask to use our create_app fuction (factory)
# now our app will be name "APP"
APP = create_app()