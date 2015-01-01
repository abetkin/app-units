from appunits import AppUnit as App
from appunits.util import case

a = App('a')
b = App('b', {a})
c = App('c', {a, b})

class Main(App):
    deps = {a, c}

main = Main()

units, deps_dict = main.traverse_deps()

# case.assertEqual(len(units), 3)
case.assertSequenceEqual(units, {a, b, c})

print(deps_dict)

##

main.run()
