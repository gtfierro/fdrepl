import itertools
import re
from colorama import Fore, Back, Style, init

init(autoreset = True)

version = 0
active_set = set()

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
    return attributes in get_superkeys(active_set)

def get_relation(active_set):
    all_attributes = set()
    for fd in active_set:
        all_attributes.update(fd.lhs)
        all_attributes.update(fd.rhs)
    return all_attributes

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

    # Create a dictionary to store the transitive closures of each functional dependency
    transitive_closures = {fd: {fd} for fd in active_set}

    new_active_set = active_set.copy()
    for fd1 in active_set:
        for fd2 in active_set:
            if fd1 != fd2 and fd1.rhs == fd2.lhs:
                new_fd = FunctionalDependency(fd1.lhs, fd2.rhs, new_version)
                if new_fd not in new_active_set and new_fd not in active_set:
                    print(f"TRANSITIVE {fd1.lhs} -> {fd1.rhs} and {fd2.lhs} -> {fd2.rhs}")
                    new_active_set.add(new_fd)

                    # Update the transitive closure for the new_fd
                    transitive_closures[new_fd] = transitive_closures[fd1].union(transitive_closures[fd2])

    # Update the transitive closures for all functional dependencies in the new_active_set
    for fd in new_active_set:
        if fd not in transitive_closures:
            transitive_closures[fd] = {fd}

    active_set.update(new_active_set)
    version = new_version

    return transitive_closures

def combine(active_set):
    global version
    new_version = version + 1
    new_active_set = []

    # Maintain a set of attributes that have been considered for combining
    combined_attributes = set()

    for fd1 in active_set:
        for fd2 in active_set:
            if fd1 != fd2 and fd1.lhs.issuperset(fd2.lhs):
                # Calculate the new_lhs by union of lhs of both FDs
                new_lhs = fd1.lhs.union(fd2.lhs)
                # Calculate the new_rhs by union of rhs of both FDs
                new_rhs = fd1.rhs.union(fd2.rhs)

                # Check if new_lhs and new_rhs have not been considered before
                if new_lhs not in combined_attributes and new_rhs not in combined_attributes:
                    combined_attributes.add(frozenset(new_lhs))
                    combined_attributes.add(frozenset(new_rhs))

                    new_fd = FunctionalDependency(new_lhs, new_rhs, new_version)
                    if new_fd not in new_active_set and new_fd not in active_set:
                        print(f"COMBINE {fd1} AND {fd2}")
                        new_active_set.append(new_fd)

    active_set.update(set(new_active_set))
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
    reflexive(active_set)
    while True:
        initial_length = len(active_set)
        transitive(active_set)
        combine(active_set)
        split(active_set)
        if len(active_set) == initial_length:
            break

def is_key(attributes, active_set):
    # Check if the given set of attributes is a superkey
    if not is_superkey(attributes, active_set):
        return False

    # Check if there is no proper subset of the attributes that is a superkey
    for subset_size in range(1, len(attributes)):
        for subset in itertools.combinations(attributes, subset_size):
            if is_superkey(set(subset), active_set):
                return False

    return True

def is_2nf(active_set):
    key = get_superkeys(active_set)[0]

    # non-key attribute
    all_attributes = set()
    for fd in active_set:
        all_attributes.update(fd.lhs)
        all_attributes.update(fd.rhs)

    non_key_attributes = all_attributes - key

    # Check if non-prime attributes are fully functionally dependent on the candidate key(s)
    not_2nf = False
    for fd in active_set:
        if fd.lhs != key and fd.lhs.issubset(key) and fd.rhs.intersection(non_key_attributes):
            print(f"{Fore.RED}Functional Dependency {fd.lhs} -> {fd.rhs} violates 2NF.")
            not_2nf = True
    if not_2nf:
        return False

    # If no violations found, the relation is in 2NF
    print(Fore.GREEN + "The relation is in 2NF.")
    return True

def is_3nf(active_set):
    key = get_superkeys(active_set)[0]

    if not is_2nf(active_set):
        print(Fore.RED + "Relation is not in 3NF because it is not in 2NF")
        return False

    # non-key attribute
    all_attributes = set()
    for fd in active_set:
        all_attributes.update(fd.lhs)
        all_attributes.update(fd.rhs)

    non_key_attributes = all_attributes - key

    key_fds = {fd for fd in active_set if fd.lhs == key}

    for attr in non_key_attributes:
        for fd in key_fds:
            if {attr} == fd.rhs and attr not in fd.lhs and fd.version > 1:
                print(f"{Fore.RED}{attr} is transitively dependent on the key {key} but is not directly dependent, so {fd} violates 3NF")
                return False

    # If no violations found, the relation is in 3NF
    print(Fore.GREEN + "The relation is in 3NF.")
    return True


def is_bcnf(active_set):
    if not is_3nf(active_set):
        print(Fore.RED+"Relation is not in BCNF because it is not in 3NF")
        return False
    for fd in active_set:
        if fd.trivial:
            continue
        if not is_superkey(fd.lhs, active_set):
            print(Fore.RED + f"{fd}'s lhs is not a superkey, so this is not BCNF")
            return False

    print(Fore.GREEN + "The relation is in BCNF")
    return True

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
    elif command.startswith("is-superkey "):
        attrs = {s.strip() for s in re.sub(r'[{}]', '', command[12:]).split(',')}
        if is_superkey(attrs, active_set):
            print(f"{Fore.GREEN}{attrs} is a superkey.")
        else:
            print(f"{Fore.RED}{attrs} is not a superkey.")
    elif command.startswith("is-key "):
        attrs = {s.strip() for s in re.sub(r'[{}]', '', command[8:]).split(',')}
        if is_key(attrs, active_set):
            print(f"{Fore.GREEN}{attrs} is a key.")
        else:
            print(f"{Fore.RED}{attrs} is not a key.")
    elif command == "relation":
        print(get_relation(active_set))
    elif command == "is_2nf":
        is_2nf(active_set)
    elif command == "is_3nf":
        is_3nf(active_set)
    elif command == "is_bcnf":
        is_bcnf(active_set)
    elif command == "show" or command == "fds":
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
    elif command == "help":
        print("Commands:")
        print("  'reflexive' (applies reflexive rule to existing functional dependencies)")
        print("  'closure {a,b,c}' (computes closure of the given set of attributes)")
        print("  'transitive' (applies transitive rule to existing functional dependencies)")
        print("  'combine' (applies combine rule to existing functional dependencies)")
        print("  'split' (applies split rule to existing functional dependencies)")
        print("  'push {a,b} -> {c,d}' (adds a new functional dependency)")
        print("  'apply-closure-rules' (applies closure rules until no new entries are added)")
        print("  'get-superkeys' (prints all superkeys of the current set of functional dependencies)")
        print("  'is-superkey {a,b,c}' (checks if the given set of attributes is a superkey)")
        print("  'is-key {a,b,c}' (checks if the given set of attributes is a key)")
        print("  'relation' (prints all attributes in the current set of functional dependencies)")
        print("  'is_2nf' (checks if the current set of functional dependencies is in 2NF)")
        print("  'is_3nf' (checks if the current set of functional dependencies is in 3NF)")
        print("  'is_bcnf' (checks if the current set of functional dependencies is in BCNF)")
        print("  'show' (prints the current set of functional dependencies)")
        print("  'load <file_path>' (loads commands from the given file)")
        print("  'save <file_path>' (saves the current set of commands to the given file)")
        print("  'quit' (exits the program)")
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
    command_history = []

    while True:
        command = input(Fore.CYAN + "Enter a command:" + Style.RESET_ALL + "\n> ").strip()
        command_history.append(command)

        if not execute_command(command, active_set, version):
            break


if __name__ == "__main__":
    main()

