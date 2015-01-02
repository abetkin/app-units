
from appunits import mark, AppUnit

class custom(mark):

    def build(self, app):
        if self.source_function:
            return int(self.source_function())
        return int(self.value)


class MarkedApp(AppUnit):

    mark1 = mark2 = custom(value=1)

    @custom()
    def mark3(owner):
        return 2

print(MarkedApp._marks)