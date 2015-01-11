from appunits import AppUnit as App
from appunits.util import case

lines = []

class A(App):

    def run(self):
        lines.append('A')

class B(App):
    depends_on = [A]

    def run(self):
        lines.append('B')


class C(App):
    depends_on = [B]
    autorun_dependencies = False

    def run(self):
        self.all_units[B].main()
        lines.append('C')


class Main(App):
    depends_on = [C]

    def run(self):
        lines.append('D')


main = Main.make()

main.run(stop_after=A)
case.assertSequenceEqual(lines, ['A'])
main.run(stop_after=B)
case.assertSequenceEqual(lines, ['A'])

main.run(stop_after=C)
case.assertSequenceEqual(lines, ['A', 'B', 'C'])
main.run()
case.assertSequenceEqual(lines, ['A', 'B', 'C', 'D'])

