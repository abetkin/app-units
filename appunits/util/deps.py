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
