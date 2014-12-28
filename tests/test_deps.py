from appunits import AppUnit as App
from appunits.util import case

a = App('a', [])
b = App('b', [a])
c = App('c', [a, b])

units = App.reorder([a, c])

case.assertSequenceEqual(units, [a, b, c])