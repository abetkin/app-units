import os
from pathlib import Path

proj_dir = Path(__file__) / '..' / '..' / 'examples' / 'dj'

os.chdir(str(proj_dir.resolve()))
os.environ['DJANGO_SETTINGS_MODULE'] = 'dj.settings'
import django
django.setup()

from app.views import Serialize
from appunits import Unit

# TODO adapters
class Params:
    publish_attrs = ('request_params',)

    request_params = {
        'name': 'gav',
        'happy': True,
    }

app = Unit.make('main', [Serialize], [Params])
app.run()
print(app.deps[Serialize].result)
