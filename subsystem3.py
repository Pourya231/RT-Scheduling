import threading
import queue
from subsystem1 import Subsystem1 , TaskSubsystem1
from subsystem2 import Subsystem2 , TaskSubsystem2


class TaskSubsystem3:
    def __init__(self, name, burst_time, resource1_usage, resource2_usage, arrival_time, period, num_repetitions):
        self.name = name  # Task name
        self.burst_time = burst_time  # Fixed execution duration
        self.resource1_usage = resource1_usage  # Resource R1 usage
        self.resource2_usage = resource2_usage  # Resource R2 usage
        self.arrival_time = arrival_time  # Arrival time of the task
        self.period = period  # Task period
        self.num_repetitions = num_repetitions  # Number of repetitions of the task
        self.remaining_time = burst_time  # Remaining execution time for the current repetition
        self.next_release_time = arrival_time  # Next release time for the task
        self.repetitions_completed = 0  # Number of completed repetitions
        self.status = "Waiting"  # Initial status of the task
        self.missed_deadlines = 0  # Count of missed deadlines

    def is_ready(self):
        """Check if the task is ready to execute."""
        return self.repetitions_completed < self.num_repetitions

    def __repr__(self):
        return (f"Task {self.name} (burst_time={self.burst_time}, period={self.period}, arrival_time={self.arrival_time}, "
                f"remaining_time={self.remaining_time}, repetitions_completed={self.repetitions_completed}, "
                f"R1={self.resource1_usage}, R2={self.resource2_usage})")

    def __lt__(self, other):
        """Priority comparison based on the task's period."""
        return self.period < other.period

class Processor(threading.Thread):
    def __init__(self, id, subsystem):
        super().__init__()
        self.id = id  # Processor ID
        self.subsystem = subsystem  # Associated subsystem
        self.running_task = None  # Current running task
        self.lock = threading.Lock()  # Lock for managing shared resources

    def run(self):
        """Run the processor until the subsystem's max time is reached."""
        while self.subsystem.time < self.subsystem.max_time:
            self.run_for_one_time_unit()

    def run_for_one_time_unit(self):
        """Execute one time unit for the processor."""
        with self.lock:
            # Fetch a task from the ready queue
            if not self.subsystem.ready_queue.empty():
                task = self.subsystem.ready_queue.get()

                # Allocate the task to the processor
                if self.allocate_task(task):
                    self.subsystem.log(f"Processor {self.id}: Running {task}")

                    # Decrease remaining time for the current task
                    self.running_task.remaining_time -= 1

                    # Check if the task is completed
                    if self.running_task.remaining_time <= 0:
                        self.subsystem.log(
                            f"Processor {self.id}: Task {self.running_task.name} completed execution."
                        )
                        self.running_task.repetitions_completed += 1

                        # Check if the task has more repetitions
                        if self.running_task.repetitions_completed < self.running_task.num_repetitions:
                            self.running_task.remaining_time = self.running_task.burst_time
                            self.running_task.next_release_time += self.running_task.period
                            self.running_task.status = "Waiting"
                            self.subsystem.log(
                                f"Processor {self.id}: Task {self.running_task.name} is rescheduled for next release at time {self.running_task.next_release_time}."
                            )
                            self.subsystem.ready_queue.put(self.running_task)
                        else:
                            self.running_task.status = "Completed"
                            self.subsystem.finished_tasks.append(self.running_task)
                            self.subsystem.log(
                                f"Processor {self.id}: Task {self.running_task.name} has finished all repetitions."
                            )
                        self.release_resources()
                        self.running_task = None
                else:
                    # Reinsert the task into the ready queue if it couldn't be allocated
                    self.subsystem.ready_queue.put(task)

    def allocate_task(self, task):
        """Allocate a task to the processor if resources are available."""
        if self.running_task is None or task.period < self.running_task.period:
            # Preempt the current task if necessary
            if self.running_task:
                self.subsystem.log(
                    f"Processor {self.id}: Preempting {self.running_task.name} for higher-priority task {task.name}."
                )
                self.subsystem.ready_queue.put(self.running_task)
                self.release_resources()

            # Check resource availability and allocate if possible
            if self.subsystem.allocate_resources(task):
                self.running_task = task
                self.running_task.status = "Running"
                self.subsystem.log(f"Processor {self.id}: Allocated resources for {task.name}.")
                return True
            else:
                self.subsystem.log(f"Processor {self.id}: Insufficient resources for {task.name}.")
                return False
        return False

    def release_resources(self):
        """Release resources allocated to the current task."""
        if self.running_task:
            self.subsystem.release_resources(self.running_task)
            self.subsystem.log(f"Processor {self.id}: Released resources for {self.running_task.name}.")
            self.running_task = None
class Subsystem3(threading.Thread):
    def __init__(self, max_time, subsystem1, subsystem2, r1_initial, r2_initial):
        super().__init__()
        self.ready_queue = queue.PriorityQueue()
        self.waiting_queue = queue.PriorityQueue()  # For tasks waiting for release or resources
        self.processors = []
        self.all_tasks = []
        self.finished_tasks = []
        self.time = 0
        self.max_time = max_time
        self.all_resource1 = r1_initial  # Available R1 resources
        self.all_resource2 = r2_initial  # Available R2 resources
        self.borrowed_resources_r1_s1 = 0 
        self.borrowed_resources_r1_s2 = 0
        self.borrowed_resources_r2_s1 = 0
        self.borrowed_resources_r2_s2 = 0
        self.subsystem1 = subsystem1
        self.subsystem2 = subsystem2
        self.log_file = "subsystem3.txt"
        self.lock = threading.Lock()  # Lock for resource management
        with open(self.log_file, "w") as file:
            file.write("")  # Clear the log file at the start

    def log(self, message):
        with open(self.log_file, "a") as file:
            file.write(message + "\n")
        print(message)

    def add_task(self, task):
        """Add a task to the system."""
        self.all_tasks.append(task)

    def initialize_processors(self, num_processors):
        """Initialize the processors for the subsystem."""
        for i in range(num_processors):
            processor = Processor(i + 1, self)
            self.processors.append(processor)

    def can_execute_task(self, task):
        """Check if enough R1 and R2 resources are available for a task."""
        return (
            self.all_resource1 >= task.resource1_usage and
            self.all_resource2 >= task.resource2_usage
        )

    def allocate_resources(self, task):
        """Allocate resources to a task if available."""
        with self.lock:
            if self.can_execute_task(task):
                self.all_resource1 -= task.resource1_usage
                self.all_resource2 -= task.resource2_usage
                return True
            return False

    def release_resources(self, task):
        """Release resources after task completion."""
        with self.lock:
            self.all_resource1 += task.resource1_usage
            self.all_resource2 += task.resource2_usage

    def borrow_resources(self, task):
        """Borrow resources from Subsystem1 and Subsystem2 if necessary."""
        needed_r1 = max(0, task.resource1_usage - self.all_resource1)
        needed_r2 = max(0, task.resource2_usage - self.all_resource2)

        with self.lock:
            if needed_r1 > 0 and self.subsystem1.all_resource1 >= needed_r1:
                self.subsystem1.all_resource1 -= needed_r1
                self.all_resource1 += needed_r1
                self.borrowed_resources_r1_s1 += needed_r1
                self.log(f"Borrowed {needed_r1} R1 from Subsystem1 for task {task.name}")

            if needed_r1 > 0 and self.subsystem2.all_resource2 >= needed_r1:
                self.subsystem2.all_resource1 -= needed_r1
                self.all_resource1 += needed_r1
                self.borrowed_resources_r1_s2 += needed_r1
                self.log(f"Borrowed {needed_r1} R1 from Subsystem2 for task {task.name}")
                
            if needed_r2 > 0 and self.subsystem1.all_resource2 >= needed_r2:
                self.subsystem1.all_resource2 -= needed_r2
                self.all_resource2 += needed_r2
                self.borrowed_resources_r2_s1 += needed_r2
                self.log(f"Borrowed {needed_r2} R2 from Subsystem1 for task {task.name}")

            if needed_r2 > 0 and self.subsystem2.all_resource2 >= needed_r2:
                self.subsystem2.all_resource2 -= needed_r2
                self.all_resource2 += needed_r2
                self.borrowed_resources_r2_s2 += needed_r2
                self.log(f"Borrowed {needed_r2} R2 from Subsystem2 for task {task.name}")

    def return_resources(self, task):
        """Return borrowed resources to Subsystem1 and Subsystem2."""
        with self.lock:
            if self.borrowed_resources_r1_s2 > 0:
                returned_r1 = min(self.borrowed_resources_r1_s2 , task.resource1_usage)
                self.subsystem2.all_resource1 += returned_r1
                self.all_resource1 -= returned_r1
                self.borrowed_resources_r1_s2 -= returned_r1
                self.log(f"Returned {returned_r1} R1 to Subsystem2.")

            if self.borrowed_resources_r2_s2 > 0:
                returned_r2 = min(self.borrowed_resources_r2_s2, task.resource2_usage)
                self.subsystem2.all_resource2 += returned_r2
                self.all_resource2 -= returned_r2
                self.borrowed_resources_r2_s2 -= returned_r2
                self.log(f"Returned {returned_r2} R2 to Subsystem2.")
                
            if self.borrowed_resources_r1_s1 > 0:
                returned_r1 = min(self.borrowed_resources_r1_s1, task.resource1_usage)
                self.subsystem1.all_resource1 += returned_r1
                self.all_resource1 -= returned_r1
                self.borrowed_resources_r1_s1 -= returned_r1
                self.log(f"Returned {returned_r1} R1 to Subsystem1.")

            if self.borrowed_resources_r2_s1 > 0:
                returned_r2 = min(self.borrowed_resources_r2_s1, task.resource2_usage)
                self.subsystem1.all_resource2 += returned_r2
                self.all_resource2 -= returned_r2
                self.borrowed_resources_r2_s1 -= returned_r2
                self.log(f"Returned {returned_r2} R2 to Subsystem1.")

    def run(self):
        while self.time < self.max_time:
            self.log(f"Time {self.time}")

            # Release and re-release tasks based on arrival and period
            for task in self.all_tasks:
                if task.repetitions_completed < task.num_repetitions and task.next_release_time == self.time:
                    task.remaining_time = task.burst_time
                    task.next_release_time += task.period
                    if self.allocate_resources(task):
                        self.ready_queue.put(task)
                        self.log(f"Task {task.name} released to ready queue at time {self.time}")
                    else:
                        self.waiting_queue.put(task)
                        self.log(f"Task {task.name} moved to waiting queue due to insufficient resources.")

            # Check waiting queue for tasks that can now run
            with self.lock:
                for task in list(self.waiting_queue.queue):
                    if self.allocate_resources(task):
                        self.ready_queue.put(task)
                        self.waiting_queue.queue.remove(task)
                        self.log(f"Task {task.name} moved to ready queue from waiting queue.")

            # Execute tasks on processors
            threads = []
            for processor in self.processors:
                thread = threading.Thread(target=processor.run_for_one_time_unit)
                threads.append(thread)
                thread.start()

            for thread in threads:
                thread.join()

            self.time += 1

        self.report()

    def report(self):
        self.log("\nSystem Report:")
        for task in self.all_tasks:
            self.log(f"Task {task.name}: Missed Deadlines = {task.missed_deadlines}")
        self.log(f"Total borrowed R1: {self.borrowed_resources_r1_s2 + self.borrowed_resources_r1_s1}")
        self.log(f"Total borrowed R2: {self.borrowed_resources_r2_s1 + self.borrowed_resources_r2_s2}")


# Example Usage
subsystem1 = Subsystem1(3, 3)
subsystem1.add_task(TaskSubsystem1(["T1", 8, 1, 1, 0, 1]))
subsystem1.add_task(TaskSubsystem1(["T2", 12, 3, 1, 1, 2]))
subsystem1.add_task(TaskSubsystem1(["T3", 10, 1, 1, 2, 3]))
subsystem1.initial_processor()

subsystem2 = Subsystem2(10, 10)
subsystem2.add_task(TaskSubsystem2(["T4", 6, 1, 1, 1]))
subsystem2.add_task(TaskSubsystem2(["T5", 3, 3, 1, 2]))
subsystem2.add_task(TaskSubsystem2(["T6", 9, 1, 1, 2]))
subsystem2.initial_processors()
subsystem3 = Subsystem3(
    max_time=50, 
    subsystem1=subsystem1,  # Initialize Subsystem1 with its R1 and R2 resources
    subsystem2=subsystem2,  # Initialize Subsystem2 with its R1 and R2 resources
    r1_initial=100, 
    r2_initial=100
)

# Adding tasks to Subsystem3 with the updated attributes
subsystem3.add_task(TaskSubsystem3(
    name="T1",
    burst_time=2,
    resource1_usage=3,
    resource2_usage=2,
    arrival_time=0,
    period=5,
    num_repetitions=5
))

subsystem3.add_task(TaskSubsystem3(
    name="T2",
    burst_time=4,
    resource1_usage=4,
    resource2_usage=3,
    arrival_time=0,
    period=10,
    num_repetitions=3
))

subsystem3.add_task(TaskSubsystem3(
    name="T3",
    burst_time=6,
    resource1_usage=5,
    resource2_usage=4,
    arrival_time=0,
    period=15,
    num_repetitions=2
))

# Initializing the processors for Subsystem3
subsystem3.initialize_processors(num_processors=1)

# Starting the subsystem
subsystem3.start()

# Waiting for the subsystem to complete execution
subsystem3.join()

# Generating the system report
subsystem3.report()