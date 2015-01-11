
from collections import OrderedDict

from appunits import Mark as mark, Unit
from appunits.util import case

class custom(mark):

    collect_into = '_numbers'

    def build_mark(self, app):
        if self.source_function:
            return int(self.source_function())
        return int(self.value)


class MarkedApp(Unit):

    mark1 = mark2 = custom(value=1)

    @custom()
    def mark3():
        return 2

case.assertSequenceEqual(
    MarkedApp._numbers,
    OrderedDict([('mark1', 1), ('mark2', 1), ('mark3', 2)]))
