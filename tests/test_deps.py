from appunits import AppUnit as App, UnitsRunner
from appunits.util import case

a = App('a', [])
b = App('b', [a])
c = App('c', [a, b])

runner = UnitsRunner([a, c])
units = runner.prepare()

case.assertEqual(len(units), 3)
case.assertSequenceEqual(
    set(units.values()),
    {a, b, c})


###

class MyApp(App):
    pass

runner = UnitsRunner([MyApp])
all_units = runner.prepare()
assert isinstance(all_units[MyApp], MyApp)
