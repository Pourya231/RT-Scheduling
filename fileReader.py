def load_data_from_file(filename):
    with open(filename, 'r') as file:
        lines = file.readlines()

    resources = []
    tasks = {"subsystem1": [], "subsystem2": [], "subsystem3": []}

    current_subsystem = None  # To keep track of which subsystem we are currently reading
    subsystem_count = 0  # Counter to track when we switch subsystems

    for line in lines:
        line = line.strip()
        if line.startswith('$'):
            # Move to the next subsystem upon encountering a separator
            subsystem_count += 1
            current_subsystem = None  # Reset to None to signify the transition
            continue  # Skip the separator line
        elif not line:  # Skip any empty lines
            continue

        if len(resources) < 3:
            # First three lines are resource declarations
            resources.append(list(map(int, line.split())))
        else:
            # Determine the current subsystem based on the counter
            if subsystem_count == 0:
                current_subsystem = "subsystem1"
            elif subsystem_count == 1:
                current_subsystem = "subsystem2"
            elif subsystem_count == 2:
                current_subsystem = "subsystem3"

            # Collect tasks for the current subsystem
            task_data = line.split()
            tasks[current_subsystem].append(task_data)

    return resources, tasks