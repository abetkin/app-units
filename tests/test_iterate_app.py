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
        self.deps[B].run()
        lines.append('C')


class Main(App):
    depends_on = [C]

    def run(self):
        lines.append('D')


main = Main.make()

main.autorun(A)
case.assertSequenceEqual(lines, ['A'])
main.autorun(B)
case.assertSequenceEqual(lines, ['A'])

main.autorun(C)
case.assertSequenceEqual(lines, ['A', 'B', 'C'])
main.autorun()
case.assertSequenceEqual(lines, ['A', 'B', 'C', 'D'])

