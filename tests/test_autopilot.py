from appunits import AppUnit as App
from appunits.util import case

class A(App):

    def autorun(self):
        print('A')

class B(App):
    depends_on = [A]
    autopilot = False

    def run(self):
        super().run(A)


class C(App):
    depends_on = [A, B]
    autopilot = False # rename: propagate_deps

    def autorun(self):
        self.deps[B].run()


class Main(App):
    depends_on = [C]

main = Main.make()

main.run()


# check STATE
