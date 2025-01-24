import threading
import queue
from subsystem1 import Subsystem1
from subsystem2 import Subsystem2

class TaskSubsystem3:
    def __init__(self, name, period, execution_time, deadline):
        self.name = name
        self.period = period
        self.execution_time = execution_time
        self.deadline = deadline
        self.remaining_time = execution_time
        self.next_release_time = 0
        self.missed_deadlines = 0

    def __repr__(self):
        return f"Task {self.name} (remaining_time={self.remaining_time})"

    def __lt__(self, other):
        return self.period < other.period  # RMS prioritizes shorter periods


class Processor(threading.Thread):
    def __init__(self, id, subsystem):
        super().__init__()
        self.id = id
        self.subsystem = subsystem
        self.running_task = None
        self.lock = threading.Lock()

    def run(self):
        while self.subsystem.time < self.subsystem.max_time:
            self.run_for_one_time_unit()

    def run_for_one_time_unit(self):
        with self.lock:
            if not self.subsystem.ready_queue.empty():
                task = self.subsystem.ready_queue.get()
                self.allocate_task(task)

                if self.running_task and self.running_task.remaining_time <= 0:
                    self.subsystem.log(f"Processor {self.id}: Task {self.running_task.name} completed execution.")
                    self.subsystem.finished_tasks.append(self.running_task)
                    self.release_resources()
                    self.running_task = None

    def allocate_task(self, task):
        if self.running_task is None or task.period < self.running_task.period:
            if self.running_task:
                self.subsystem.ready_queue.put(self.running_task)
            self.running_task = task
            self.subsystem.log(f"Processor {self.id}: Starting {task}")

        if self.running_task:
            if not self.subsystem.can_execute_task(self.running_task):
                self.subsystem.borrow_resources(self.running_task)
                self.running_task.remaining_time -= 2  # Borrowed resources execute faster
                self.subsystem.log(f"Processor {self.id}: Running {self.running_task} with borrowed resources, remaining time {self.running_task.remaining_time}")
            else:
                self.running_task.remaining_time -= 1
                self.subsystem.log(f"Processor {self.id}: Running {self.running_task}, remaining time {self.running_task.remaining_time}")

    def release_resources(self):
        if self.running_task:
            self.subsystem.return_resources(self.running_task)
            self.running_task = None


class Subsystem3(threading.Thread):
    def __init__(self, max_time, subsystem1, subsystem2):
        super().__init__()
        self.ready_queue = queue.PriorityQueue()
        self.waiting_queue = queue.PriorityQueue()  # For tasks waiting for release or resources
        self.processors = []
        self.all_tasks = []
        self.finished_tasks = []
        self.time = 0
        self.max_time = max_time
        self.resource_pool = 10  # Available resources in the subsystem
        self.borrowed_resources = 0  # Resources borrowed from other subsystems
        self.subsystem1 = subsystem1
        self.subsystem2 = subsystem2
        self.log_file = "subsystem3.txt"
        with open(self.log_file, "w") as file:
            file.write("")  # Clear the log file at the start

    def log(self, message):
        with open(self.log_file, "a") as file:
            file.write(message + "\n")
        print(message)

    def add_task(self, task):
        self.all_tasks.append(task)

    def initialize_processors(self, num_processors):
        for i in range(num_processors):
            processor = Processor(i + 1, self)
            self.processors.append(processor)

    def can_execute_task(self, task):
        return self.resource_pool >= task.execution_time

    def borrow_resources(self, task):
        needed_resources = task.execution_time - self.resource_pool
        borrowed = 0

        if self.subsystem1.resource_pool >= needed_resources:
            self.subsystem1.resource_pool -= needed_resources
            borrowed += needed_resources
            self.resource_pool += needed_resources
            self.log(f"Borrowed {needed_resources} resources from Subsystem1 for task {task.name}.")
        elif self.subsystem2.resource_pool >= needed_resources:
            self.subsystem2.resource_pool -= needed_resources
            borrowed += needed_resources
            self.resource_pool += needed_resources
            self.log(f"Borrowed {needed_resources} resources from Subsystem2 for task {task.name}.")

        self.borrowed_resources += borrowed

    def return_resources(self, task):
        if self.borrowed_resources > 0:
            returned_resources = min(self.borrowed_resources, task.execution_time)
            self.resource_pool -= returned_resources
            self.borrowed_resources -= returned_resources
            if self.subsystem1.resource_pool < self.subsystem1.all_resource1:
                self.subsystem1.resource_pool += returned_resources
                self.log(f"Returned {returned_resources} borrowed resources to Subsystem1.")
            elif self.subsystem2.resource_pool < self.subsystem2.all_resource2:
                self.subsystem2.resource_pool += returned_resources
                self.log(f"Returned {returned_resources} borrowed resources to Subsystem2.")


    def run(self):
        while self.time < self.max_time:
            self.log(f"Time {self.time}")

            for task in self.all_tasks:
                if task.next_release_time == self.time:
                    task.remaining_time = task.execution_time
                    if self.can_execute_task(task):
                        self.ready_queue.put(task)
                        self.log(f"Task {task.name} released to ready queue at time {self.time}")
                    else:
                        self.waiting_queue.put(task)
                        self.log(f"Task {task.name} moved to waiting queue at time {self.time}")

            # Check waiting queue for tasks that can now run
            for task in list(self.waiting_queue.queue):
                if self.can_execute_task(task):
                    self.ready_queue.put(task)
                    self.waiting_queue.queue.remove(task)
                    self.log(f"Task {task.name} moved to ready queue from waiting queue.")

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
        self.log(f"Total borrowed resources: {self.borrowed_resources}")

# Example Usage
subsystem = Subsystem3(max_time=50 , subsystem1=Subsystem1, subsystem2=Subsystem2)
subsystem.add_task(TaskSubsystem3("T1", period=5, execution_time=2, deadline=5))
subsystem.add_task(TaskSubsystem3("T2", period=10, execution_time=4, deadline=10))
subsystem.add_task(TaskSubsystem3("T3", period=15, execution_time=6, deadline=15))

subsystem.initialize_processors(num_processors=1)
subsystem.start()
subsystem.join()
 