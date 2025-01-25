# README

## Project Overview

This project simulates a **multi-subsystem processing environment** where each subsystem manages tasks using shared resources. The simulation consists of multiple subsystems, each with a defined set of resources and tasks to execute. The main subsystem coordinates these subsystems to ensure synchronized processing over a global clock.

---

## Project Structure

The project directory is organized as follows:

```
├── fileReader.py              # Contains functions to read input data from a file.
├── in.txt                     # Input file specifying resources and tasks.
├── mainSubsystem.py           # Main program to initialize and run the simulation.
├── subsystem1.py              # Code for Subsystem1 and its task management.
├── subsystem1.txt             # Log file for Subsystem1.
├── subsystem2.py              # Code for Subsystem2 and its task management.
├── subsystem2.txt             # Log file for Subsystem2.
├── subsystem3.py              # Code for Subsystem3 and its task management.
├── subsystem3.txt             # Log file for Subsystem3.
└── tasks_results_subsystem1.txt # Stores results for Subsystem1 tasks.
```

---

## Input File (`in.txt`)

The input file specifies the resources available for each subsystem and the tasks assigned to them. The file format is as follows:

1. **Resources**: Each line defines the resources for a subsystem in the format:
   ```
   R1 R2
   ```
   where `R1` and `R2` represent the number of resources of type 1 and type 2, respectively.

2. **Tasks**: Each subsequent line represents a task in the format:
   ```
   TaskName BurstTime R1Usage R2Usage ArrivalTime Period NumRepetitions
   ```

---

## How It Works

1. **Subsystems**:
   - **Subsystem1** and **Subsystem2** manage tasks independently using their own processors.
   - Each subsystem processes tasks using shared resources (`R1` and `R2`).

2. **Tasks**:
   - Each task is defined by its name, burst time, resource usage (`R1` and `R2`), arrival time, period, and the number of repetitions.
   - Subsystems manage task execution while ensuring resource availability.

3. **Main Subsystem**:
   - Synchronizes the execution of all subsystems to ensure they process tasks in lockstep over a global clock.

4. **FileReader**:
   - Reads the input file (`in.txt`) and provides the data to initialize the subsystems and tasks.

---

## How to Run

1. Place the input file (`in.txt`) in the project directory with the desired resource and task configurations.
2. Run the main program:
   ```bash
   python mainSubsystem.py
   ```
3. View logs for each subsystem in the corresponding log files (`subsystem1.txt`, `subsystem2.txt`, etc.).
4. For results of completed tasks, check the `tasks_results_subsystem1.txt` file and others as needed.

---

## Example `in.txt`

Below is an example `in.txt`:

```
10 10
12 8
T1 8 1 1 0 10 3
T2 12 2 2 1 12 4
T3 10 1 1 2 15 2
```

### Explanation:
- Subsystem1 has 10 units of `R1` and `R2`, and Subsystem2 has 12 units of `R1` and 8 units of `R2`.
- Three tasks are provided with their respective configurations.

---

## Notes

- **Synchronization**: The main subsystem ensures all subsystems process one time unit together.
- **Resource Management**: Tasks are executed only when the required resources (`R1` and `R2`) are available.
- **Task Preemption**: Tasks with higher priority may preempt currently running tasks.
- **Logging**: All actions and results are logged for detailed analysis.

---

## Future Enhancements

1. **Extend to Subsystem3**: Add Subsystem3 for periodic task execution with inter-subsystem resource borrowing.
2. **Dynamic Input Handling**: Enhance the file reader to support dynamic task configurations during runtime.
3. **Visualization**: Add visualization for task execution and resource utilization.

---

## Contributors

- **[Saleh govahi and pourya alvani]**


--- 

Happy coding! 🚀
