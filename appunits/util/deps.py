# http://code.activestate.com/recipes/576570-dependency-resolver/
def sort_by_deps(deps_dict):
    '''
        Dependency resolver

    "deps_dict" is a dependency dictionary in which
    the values are the dependencies of their respective keys.
    '''
    d=dict((k, set(deps_dict[k])) for k in deps_dict)
    r=[]
    while d:
        # values not in keys (items without dep)
        t=set(i for v in d.values() for i in v)-set(d.keys())
        # and keys without value (items without dep)
        t.update(k for k, v in d.items() if not v)
        # can be done right away
        r.append(t)
        # and cleaned up
        d=dict(((k, v-t) for k, v in d.items() if v))
    return r


def breadth_first(root, children=iter, all_nodes=None):
    if all_nodes is None:
        all_nodes = {} # sorry it's not a set
    queue = []

    if root not in all_nodes:
        all_nodes[root] = root
        queue.append(root)

    while queue:
        node = queue.pop(0)
        yield node

        for child in children(node):
            if child not in all_nodes:
                all_nodes[child] = child
                queue.append(child)


def depth_first(tree, children=iter):
    for node in children(tree):
        yield from depth_first(node, children)
    yield tree






if __name__=='__main__':
    d=dict(
        a=('b','c'),
        b=('c','d'),
        e=(),
        f=('c','e'),
        g=('h','f'),
        i=('f',)
    )
    print(sort_by_deps(d))
