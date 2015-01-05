from appunits import AppUnit as App
from appunits.util import case

a = App('a')
b = App('b', {a})
c = App('c', {a, b})

class Main(App):
    depends_on = {a, c}

main = Main()

main.prepare()

# case.assertEqual(len(units), 3)
case.assertSequenceEqual(list(main.deps.values()),
                         [a, b, c])

##

main.run()
