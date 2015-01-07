from appunits import AppUnit as App
from appunits.util import case

class A(App):

    def run(self):
        print('A')

class B(App):
    depends_on = [A]
    # autorun_dependencies = False

    def run(self):
        print('B')
        # self.autorun(A)


class C(App):
    depends_on = [B]
    autorun_dependencies = False

    def run(self):
        self.deps[B].run()


class Main(App):
    depends_on = [C]


main = Main.make()
print(list(main.deps.keys()))
print('#####')

main.autorun(C)


# check STATE
