import itertools
import re

version = 0

class FunctionalDependency:
    def __init__(self, lhs, rhs, version=0, trivial=False):
        self._lhs = frozenset(lhs)
        self._rhs = frozenset(rhs)
        self.version = version
        self.trivial = trivial

    @property
    def lhs(self):
        return set(self._lhs)

    @property
    def rhs(self):
        return set(self._rhs)

    def __repr__(self):
        return f'{self.version}: {{{", ".join(self.lhs)}}} -> {{{", ".join(self.rhs)}}}{" (trivial)" if self.trivial else ""}'

    def __hash__(self):
        return hash((self._lhs, self._rhs))

    def __eq__(self, other):
        if isinstance(other, FunctionalDependency):
            return self._lhs == other._lhs and self._rhs == other._rhs
        return False

def is_superkey(attributes, active_set):
    for fd in active_set:
        if not fd.lhs.issubset(attributes):
            return False
    return True

def get_superkeys(active_set):
    all_attributes = set()
    for fd in active_set:
        all_attributes.update(fd.lhs)
        all_attributes.update(fd.rhs)

    superkeys = []
    for subset_size in range(1, len(all_attributes) + 1):
        for subset in itertools.combinations(all_attributes, subset_size):
            if compute_closure(subset, active_set) == all_attributes:
                superkeys.append(set(subset))
    return superkeys

def reflexive(active_set):
    global version
    new_version = version + 1
    for fd in active_set.copy():
        new_fd = FunctionalDependency(fd.lhs.copy(), fd.lhs.copy(), new_version, True)
        if new_fd not in active_set:
            print(f"REFLEXIVE {fd=}")
            active_set.add(new_fd)
        for attr in fd.rhs:
            new_fd = FunctionalDependency(fd.lhs.union({attr}), fd.rhs.copy(), new_version, True)
            if new_fd not in active_set:
                print(f"REFLEXIVE {fd=}")
                active_set.add(new_fd)
        for attr in fd.lhs:
            new_fd = FunctionalDependency(fd.lhs.copy(), fd.rhs.union({attr}), new_version)
            if new_fd not in active_set:
                print(f"REFLEXIVE {fd=}")
                active_set.add(new_fd)
    version = new_version


def transitive(active_set):
    global version
    new_version = version + 1
    new_active_set = active_set.copy()
    for fd1 in active_set:
        for fd2 in active_set:
            if fd1 != fd2 and fd1.rhs == fd2.lhs:
                new_fd = FunctionalDependency(fd1.lhs, fd2.rhs, new_version)
                if new_fd not in new_active_set and new_fd not in active_set:
                    print(f"TRANSITIVE {fd1.lhs} -> {fd1.rhs} and {fd2.lhs} -> {fd2.rhs}")
                    new_active_set.add(new_fd)
    active_set.update(new_active_set)
    version = new_version

def combine(active_set):
    global version
    new_version = version + 1
    new_active_set = set()
    for fd1 in active_set:
        for fd2 in active_set:
            if fd1 != fd2 and fd1.lhs.issuperset(fd2.lhs):
                new_lhs = fd1.lhs.union(fd2.lhs)
                new_fd = FunctionalDependency(new_lhs, fd2.rhs.union(fd1.rhs), new_version)
                if new_fd not in new_active_set and new_fd not in active_set:
                    print(f"COMBINE {fd1} AND {fd2}")
                    new_active_set.add(new_fd)
    active_set.update(new_active_set)
    version = new_version


def split(active_set):
    global version
    new_version = version + 1
    new_active_set = set()
    for fd in active_set:
        if len(fd.rhs) > 1:
            for attribute in fd.rhs.copy():
                new_rhs = {attribute}
                new_fd = FunctionalDependency(fd.lhs.copy(), new_rhs, new_version)
                if new_fd not in new_active_set and new_fd not in active_set:
                    new_active_set.add(new_fd)
                if new_fd not in active_set:
                    print(f"SPLIT {fd.lhs} -> {fd.rhs}")
    active_set.update(new_active_set)
    version = new_version

def compute_closure(attributes, functional_dependencies):
    closure = set(attributes)
    changed = True

    while changed:
        changed = False
        for fd in functional_dependencies:
            if fd.lhs.issubset(closure) and not fd.rhs.issubset(closure):
                closure.update(fd.rhs)
                changed = True

    return closure

def closure_rules(active_set):
    while True:
        initial_length = len(active_set)
        reflexive(active_set)
        transitive(active_set)
        combine(active_set)
        split(active_set)
        if len(active_set) == initial_length:
            break

def execute_command(command, active_set, version):
    if command == "reflexive":
        reflexive(active_set)
        print("Applied reflexive rule.")
    elif command.startswith("closure "):
        attrs = {s.strip() for s in re.sub(r'[{}]', '', command[8:]).split(',')}
        print(compute_closure(attrs, active_set))
    elif command == "transitive":
        transitive(active_set)
        print("Applied transitive rule.")
    elif command == "combine":
        combine(active_set)
        print("Applied combine rule.")
    elif command == "split":
        split(active_set)
        print("Applied split rule.")
    elif command.startswith("push "):
        fd_str = command[5:]
        parts = fd_str.split("->")
        if len(parts) == 2:
            lhs = {s.strip() for s in re.sub(r'[{}]', '', parts[0]).split(',')}
            rhs = {s.strip() for s in re.sub(r'[{}]', '', parts[1]).split(',')}
            active_set.add(FunctionalDependency(lhs, rhs, version))
            print(f"Added: {fd_str}")
        else:
            print("Invalid format. Functional dependency should be in the form '{a,b} -> {c,d}'")
    elif command == "apply-closure-rules":
        closure_rules(active_set)
        print("Applied closure rules until no new entries were added.")
    elif command == "get-superkeys":
         superkeys = get_superkeys(active_set)
         if superkeys:
             print("The following sets of attributes are superkeys of all attributes in active_set:")
             for superkey in superkeys:
                 print(superkey)
         else:
             print("No superkeys found for all attributes in active_set.")
    elif command == "pop":
        if active_set:
            fd = active_set.pop()
            print(f"Popped: {fd}")
        else:
            print("Active set is empty.")
    elif command == "show":
        if active_set:
            print("Current set of functional dependencies:")
            for fd in sorted(active_set, key=lambda x: x.version):
                print(fd)
        else:
            print("Active set is empty.")
    elif command.startswith("load "):
        file_path = command[5:]
        load_commands_from_file(file_path, active_set)
    elif command.startswith("save "):
        file_path = command[5:]
        save_commands_to_file(file_path, command_history)
    elif command == "quit":
        return False
    else:
        print("Invalid command. Please try again.")
    return True


def load_commands_from_file(file_path, active_set):
    global version
    try:
        with open(file_path, "r") as file:
            version = version+1
            commands = file.readlines()
            for cmd in commands:
                cmd = cmd.strip()
                print(f"Executing command from file: {cmd}")
                if not execute_command(cmd, active_set, version):
                    break
    except FileNotFoundError:
        print(f"File not found: {file_path}")


def save_commands_to_file(file_path, command_history):
    with open(file_path, "w") as file:
        file.writelines([f"{cmd}\n" for cmd in command_history])
    print(f"Commands saved to {file_path}")


def main():
    global version
    active_set = set()
    command_history = []

    while True:
        command = input("Enter a command (push/pop/reflexive/transitive/combine/split/show/load/save/quit):\n> ").strip()
        command_history.append(command)

        if not execute_command(command, active_set, version):
            break


if __name__ == "__main__":
    main()

