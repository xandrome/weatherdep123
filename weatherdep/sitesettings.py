from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

DATABASES = {
	'default': {
		'ENGINE': 'django.db.backends.postgresql',
		'NAME': 'weatherdep',
		'USER': 'postgres',
		'PASSWORD': 'maciek22',
		'HOST': 'localhost',
		'PORT': '5432',
		}
}

OPENWEATHER_KEY = '5fbdba73c8eb4c39229dab819cc223b5'
