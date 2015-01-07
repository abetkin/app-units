import os
from pathlib import Path

proj_dir = Path(__file__) / '..' / '..' / 'examples' / 'dj'

os.chdir(str(proj_dir.resolve()))
os.environ['DJANGO_SETTINGS_MODULE'] = 'dj.settings'
import django
django.setup()

from app.views import Serialize
from appunits import AppUnit

# TODO adapters
class Params:
    share_context = True
    published_context = ('request_params',)

    request_params = {
        'name': 'gav',
        'happy': True,
    }

app = AppUnit.make('main', [Serialize], [Params])
app.autorun()
print(app.deps[Serialize].result)
