# fd-repl

```bash
pip install fdrepl
```

Start by running `fdrepl` in the command line.

```
> load fds/test
Executing command from file: push {a,b} -> {c}
Added: {a,b} -> {c}
Executing command from file: push {b} -> {d}
Added: {b} -> {d}
Enter a command:
> show
Current set of functional dependencies:
1: {b, a} -> {c}
1: {b} -> {d}
Enter a command:
> combine
COMBINE 1: {b, a} -> {c} AND 1: {b} -> {d}
Applied combine rule.
Enter a command:
> show
Current set of functional dependencies:
1: {b, a} -> {c}
1: {b} -> {d}
2: {b, a} -> {c, d}
Enter a command:
> is-key {a,b}
{'b', 'a'} is a key.
```

REPL for playing around with functional dependencies, their closures, and levels of normalization.

Created in an evening by [@gtfierro](http://home.gtf.fyi) and ChatGPT.

![](.github/demo.gif)
