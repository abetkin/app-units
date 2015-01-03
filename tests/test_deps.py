from appunits import AppUnit as App
from appunits.util import case

a = App('a')
b = App('b', {a})
c = App('c', {a, b})

class Main(App):
    deps = {a, c}

main = Main()

main.prepare()

# case.assertEqual(len(units), 3)
case.assertSequenceEqual(main.deps, [a, b, c])

##

main.run()
