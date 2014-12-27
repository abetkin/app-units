from appunits import UnitsRunner, AppUnit as App
from appunits.util import case

a = App([], 'a')
b = App([a], 'b')
c = App([a, b], 'c')

runner = UnitsRunner([a, c])

case.assertSequenceEqual(
    runner.get_units_order(),
    [a, b, c])