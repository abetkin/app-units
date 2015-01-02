
from collections import OrderedDict

from appunits import Mark as mark, AppUnit
from appunits.util import case

class custom(mark):

    COLLECT_INTO = '_numbers'

    def build(self, app):
        if self.source_function:
            return int(self.source_function())
        return int(self.value)


class MarkedApp(AppUnit):

    mark1 = mark2 = custom(value=1)

    @custom()
    def mark3():
        return 2

case.assertSequenceEqual(
    MarkedApp._numbers,
    OrderedDict([('mark1', 1), ('mark2', 1), ('mark3', 2)]))
