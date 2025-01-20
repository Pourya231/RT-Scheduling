import threading
import queue
import time
import random

# Task structure
class Task:
    def __init__(self, task_id, arrival_time, execution_time, priority=0, resources_required=[]):
        self.task_id = task_id
        self.arrival_time = arrival_time
        self.execution_time = execution_time
        self.remaining_time = execution_time
        self.priority = priority
        self.resources_required = resources_required
        self.state = "Ready"

# Subsystem base class
class Subsystem(threading.Thread):
    def __init__(self, subsystem_id, scheduling_algorithm, available_resources):
        super().__init__()
        self.subsystem_id = subsystem_id
        self.scheduling_algorithm = scheduling_algorithm
        self.ready_queue = queue.PriorityQueue()
        self.waiting_queue = queue.Queue()
        self.tasks = []
        self.lock = threading.Lock()
        self.available_resources = available_resources
        self.current_time_unit = 0

    def add_task(self, task):
        with self.lock:
            # Check if resources are available
            if all(self.available_resources.get(r, 0) > 0 for r in task.resources_required):
                for r in task.resources_required:
                    self.available_resources[r] -= 1  # Reserve resources
                self.ready_queue.put((task.priority, task))
                print(f"Subsystem {self.subsystem_id}: Task {task.task_id} added to Ready Queue.")
            else:
                self.waiting_queue.put(task)
                print(f"Subsystem {self.subsystem_id}: Task {task.task_id} added to Waiting Queue.")

    def process_waiting_queue(self):
        with self.lock:
            temp_queue = queue.Queue()
            while not self.waiting_queue.empty():
                task = self.waiting_queue.get()
                if all(self.available_resources.get(r, 0) > 0 for r in task.resources_required):
                    for r in task.resources_required:
                        self.available_resources[r] -= 1  # Reserve resources
                    self.ready_queue.put((task.priority, task))
                    print(f"Subsystem {self.subsystem_id}: Task {task.task_id} moved to Ready Queue.")
                else:
                    temp_queue.put(task)
            self.waiting_queue = temp_queue

    def run(self):
        while True:
            self.process_waiting_queue()
            if not self.ready_queue.empty():
                _, task = self.ready_queue.get()
                print(f"Subsystem {self.subsystem_id}: Executing Task {task.task_id} at time unit {self.current_time_unit}")
                task.state = "Running"
                # Simulate execution
                time.sleep(1)  # Simulate one time unit
                task.remaining_time -= 1
                if task.remaining_time <= 0:
                    print(f"Subsystem {self.subsystem_id}: Completed Task {task.task_id}.")
                    task.state = "Completed"
                    # Release resources after execution
                    for r in task.resources_required:
                        self.available_resources[r] += 1
                else:
                    # Re-queue the task if not completed
                    self.ready_queue.put((task.priority, task))
                    print(f"Subsystem {self.subsystem_id}: Task {task.task_id} re-queued with {task.remaining_time} time units remaining.")
            else:
                time.sleep(1)  # Idle waiting for tasks

# Specific Subsystems with different scheduling algorithms
class RealTimeSubsystem(Subsystem):
    def __init__(self, available_resources):
        super().__init__(1, "Rate Monotonic", available_resources)

class ShortestRemainingTimeSubsystem(Subsystem):
    def __init__(self, available_resources):
        super().__init__(2, "Shortest Remaining Time First", available_resources)

    def add_task(self, task):
        with self.lock:
            # Use remaining time as priority for SRTF
            if all(self.available_resources.get(r, 0) > 0 for r in task.resources_required):
                for r in task.resources_required:
                    self.available_resources[r] -= 1  # Reserve resources
                self.ready_queue.put((task.remaining_time, task))
                print(f"Subsystem {self.subsystem_id}: Task {task.task_id} added to Ready Queue.")
            else:
                self.waiting_queue.put(task)
                print(f"Subsystem {self.subsystem_id}: Task {task.task_id} added to Waiting Queue.")

class WeightedRoundRobinSubsystem(Subsystem):
    def __init__(self, available_resources):
        super().__init__(3, "Weighted Round Robin", available_resources)
        self.time_slice = 2

# Main thread to coordinate subsystems
class MainSystem:
    def __init__(self):
        self.available_resources = {"R1": 2, "R2": 2}  # Example resources
        self.subsystems = [
            RealTimeSubsystem(self.available_resources),
            ShortestRemainingTimeSubsystem(self.available_resources),
            WeightedRoundRobinSubsystem(self.available_resources)
        ]
        self.time_unit = 0
        self.lock = threading.Lock()

    def synchronize_subsystems(self):
        while True:
            with self.lock:
                self.time_unit += 1
                print(f"MainSystem: Advancing to time unit {self.time_unit}.")
                for subsystem in self.subsystems:
                    subsystem.current_time_unit = self.time_unit
            time.sleep(1)  # Simulate a single time unit

    def start(self):
        for subsystem in self.subsystems:
            subsystem.start()
        # Synchronize subsystems
        sync_thread = threading.Thread(target=self.synchronize_subsystems)
        sync_thread.start()

    def stop(self):
        for subsystem in self.subsystems:
            subsystem.join()

if __name__ == "__main__":
    main_system = MainSystem()

    # Example tasks
    tasks = [
        Task(task_id=1, arrival_time=0, execution_time=3, priority=1, resources_required=["R1"]),
        Task(task_id=2, arrival_time=1, execution_time=5, priority=2, resources_required=["R2"]),
        Task(task_id=3, arrival_time=2, execution_time=2, priority=1, resources_required=["R1", "R2"]),
    ]

    # Assign tasks to subsystems
    main_system.subsystems[0].add_task(tasks[0])  # Real-time subsystem
    main_system.subsystems[1].add_task(tasks[1])  # SRTF subsystem
    main_system.subsystems[2].add_task(tasks[2])  # Weighted Round Robin subsystem

    # Start the system
    main_system.start()
