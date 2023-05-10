import os
import configparser
import sys
def run():

    while not configfile_exists():
        setup()
    config = configparser.ConfigParser()
    config.read(get_configpath())
    todofilepath = config['PATHS']['Todofilepath']

    todos = parse_todo_file(todofilepath)
    todos = sort_default(todos)
    welcome(todofilepath)
    command = '0'
    while command != 'q':
        print("Command: ")
        command=input()
        todos = do_action(command, todos)




#------------------------------------------------------------------------------
# Actions
#------------------------------------------------------------------------------        
def do_action(command, todos):
    if command=='ls':
        print_todos([td for td in todos if not td['Done']])
    if command=='raw':
        print(todos)
    return todos



#------------------------------------------------------------------------------
# Visualization
#------------------------------------------------------------------------------


def resetting_page(f):
    def wrapper(*args, **kwargs):
        print("\033[H\033[J", end="")
        print(
        """
			   _____  ___   ____    ___  
			  |_   _|/ _ \ |  _ \  / _ \ 
			    | | | | | || | | || | | |
			    | | | |_| || |_| || |_| |
			    |_|  \___/ |____/  \___/ 
        """)
        
        print("________________________________________________________________________________")
        res=f(*args, **kwargs)
        print("\n")
        print("________________________________________________________________________________")
        print("\n\n\n\n")
        return res
    return wrapper

@resetting_page
def welcome(path):
    print(f"Todo.txt file loaded: {path}")


@resetting_page
def print_raw(todos):
    print(todos)


@resetting_page
def print_todos(todos):
    # Iterate over the to-do items and print each one
    for i, todo in enumerate(todos):
        print("\n")
        print(f"{i}. ", end="")  # Print the index of the item with no label
        if todo['Done']:
            print(f"[✔] {todo['Description']} ({todo['CompletedAt']})")
        else:
            print(f"[ ] {todo['Description']}")
        if todo['Priority']:
            print(f"    🔥 Priority: {todo['Priority']}")
        if todo['DueTo']:
            print(f"    📆 Due to: {todo['DueTo']}")
        if todo['Projects']:
            print(f"    📦 Projects: {', '.join(todo['Projects'])}")
        if todo['Contexts']:
            print(f"    📍 Contexts: {', '.join(todo['Contexts'])}")
        for key, value in todo.items():
            if key not in {'Done', 'Description', 'Priority', 'DueTo', 'Projects', 'Contexts', 'CreatedAt', 'CompletedAt'} and value:
                print(f"    {key}: {value}")

#------------------------------------------------------------------------------
# Sorting
#------------------------------------------------------------------------------
from datetime import datetime

def sort_default(todos):
    # First, sort the to-do items that have a priority
    priority_todos = [todo for todo in todos if todo['Priority'] and not todo['Done']]
    priority_todos.sort(key=lambda x: (x['Priority'], x['Projects'], x['DueTo'] or ''))

    # Then, sort the to-do items that don't have a priority
    non_priority_todos = [todo for todo in todos if not todo['Priority'] and not todo['Done']]
    non_priority_todos.sort(key=lambda x: (x['Projects'], x['DueTo'] or ''))

    # Finally, sort the completed to-do items by completion date
    completed_todos = [todo for todo in todos if todo['Done']]
    completed_todos.sort(key=lambda x: datetime.strptime(x['CompletedAt'], '%Y-%m-%d'), reverse=True)

    # Concatenate the three lists of to-do items and return the result
    return  priority_todos + non_priority_todos +completed_todos

#------------------------------------------------------------------------------
# Writer
#------------------------------------------------------------------------------
def generate_todo_file(todos):
    # Create an empty string to hold the contents of the file

    file_contents = ''
    for todo in todos:
        file_contents += generate_todo_line(todo) + '\n'

    return file_contents


def generate_todo_line(todo):
    s = ''
    # If the to-do item is marked as completed, add the completed date
    # to the beginning of the line
    if todo['Done']:
        s += 'x ' + todo['CompletedAt'] + ' '

    # If the to-do item has a priority, add it to the beginning of the line
    if todo['Priority']:
        s += '(' + todo['Priority'] + ') '

    # Add the description of the to-do item to the line
    s += todo['Description']

    # If the to-do item has a due date, add it to the end of the line
    if todo['DueTo']:
        s += ' ' + todo['DueTo']

    # If the to-do item has any projects, add them to the line
    if todo['Projects']:
        projects = todo['Projects'].split('#')
        for project in projects:
            s += ' +' + project

    # If the to-do item has any contexts, add them to the line
    if todo['Contexts']:
        contexts = todo['Contexts'].split('@')
        for context in contexts:
            s += ' @' + context

    # Add any other metadata tags to the line
    for key, value in todo.items():
        if key not in [
                'Done', 'Description', 'CreatedAt', 'CompletedAt', 'DueTo',
                'Priority', 'Projects', 'Contexts'
        ]:
            s += ' ' + key + ':' + value

    return s


#------------------------------------------------------------------------------
# Parser
#------------------------------------------------------------------------------
import re


def parse_todo_file(path):
    # Read the contents of the file into a list of strings
    with open(path, 'r') as file:
        lines = file.readlines()

    # Create an empty list to hold the to-do items
    todos = []

    # Iterate over each line in the file
    for line in lines:
        todo_dict = parse_todo_line(line)
        # Add the dictionary for this to-do item to the list of todos
        todos.append(todo_dict)

    return todos


def parse_todo_line(line):
    # Remove any leading/trailing whitespace from the line
    line = line.strip()

    # If the line starts with 'x ', the to-do item is marked as completed
    # and the completed date is extracted from the line
    if line.startswith('x '):
        completed_at, line = line[2:12], line[13:]
    else:
        completed_at = ''

    # If the line starts with a priority indicator (e.g. '(A)'), extract the
    # priority and remove it from the description
    m = re.search(r'^\(([A-Z])\) (.*)$', line)
    if m:
        priority, line = m.group(1), m.group(2)
    else:
        priority = ''

    # If the line ends with a due date (e.g. '2023-05-31'), extract it and
    # remove it from the description
    m = re.search(r'^(.*?) (\d{4}-\d{2}-\d{2})$', line)
    if m:
        description, due_to = m.group(1), m.group(2)
    else:
        description, due_to = line, ''

    # Extract any contexts from the line (e.g. '@home')
    m = re.findall(r' @(\S+)', line)
    contexts = ' '.join([context[1:] for context in m])

    # Extract any projects from the line (e.g. '+work')
    m = re.findall(r' \+(\S+)', line)
    projects = ' '.join([project[1:] for project in m])

    # Extract any other metadata tags from the line (e.g. 'tag:value')
    tags = re.findall(r' ([^@+\s]\S*:\S+)', line)

    # Create a dictionary to hold the extracted information for this to-do item
    todo_dict = {
        'Done': True if completed_at else False,
        'Description': description,
        'CreatedAt': '',
        'CompletedAt': completed_at,
        'DueTo': due_to,
        'Priority': priority,
        'Projects': projects,
        'Contexts': contexts,
    }
    # Add any metadata tags to the dictionary
    for tag in tags:
        key, value = tag.split(':')
        todo_dict[key] = value

    return todo_dict


#------------------------------------------------------------------------------
# Setup and Config
#------------------------------------------------------------------------------


def get_homepath():
    home_folder = os.path.expanduser("~")
    return home_folder


def get_configpath():
    filename = ".todopysrc"
    homepath = get_homepath()
    return os.path.join(homepath, filename)


def configfile_exists():
    return os.path.isfile(get_configpath())


def setup():
    print("Setup todo.py")
    confpath = get_configpath()

    if configfile_exists():
        print(f"Setup failed. A config file already exists in {confpath}")

    # Ask the user for the full path of the todo.txt file
    print("Insert todo.txt file full path: ")
    todofilepath = os.path.abspath(input())
    print(f"Todofilepath set to: {todofilepath}")

    config = configparser.ConfigParser()
    config['PATHS'] = {"Todofilepath": str(todofilepath)}

    with open(confpath, 'w') as configfile:
        config.write(configfile)

    print(f"Setup file {confpath} created successfully")
    return


#------------------------------------------------------------------------------
# Run
#------------------------------------------------------------------------------

if __name__=='__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    run()