import environ
from .base import *

env = environ.Env()

DEBUG = False


ALLOWED_HOSTS = env.list("ALLOWED_HOSTS")
SECRET_KEY = env("SECRET_KEY")

DATABASES = {
    'default': env.db("DATABASE_URL")
}