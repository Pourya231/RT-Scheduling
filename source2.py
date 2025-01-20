import threading
import queue
import time
import random

# Task structure
class Task:
    def __init__(self, task_id, arrival_time, execution_time, priority=0):
        self.task_id = task_id
        self.arrival_time = arrival_time
        self.execution_time = execution_time
        self.remaining_time = execution_time
        self.priority = priority
        self.state = "Ready"

# Subsystem 1: Real-Time Scheduling (Rate Monotonic)
class Subsystem1(threading.Thread):
    def __init__(self, tasks, time_unit):
        super().__init__()
        self.tasks = sorted(tasks, key=lambda x: x.priority)
        self.time_unit = time_unit
        self.ready_queue = queue.PriorityQueue()
        self.waiting_queue = queue.Queue()

    def run(self):
        while self.tasks:
            current_task = self.tasks.pop(0)
            if current_task.remaining_time <= self.time_unit:
                print(f"Task {current_task.task_id} completed.")
                time.sleep(current_task.remaining_time)
            else:
                current_task.remaining_time -= self.time_unit
                print(f"Task {current_task.task_id} preempted with {current_task.remaining_time} time remaining.")
                self.tasks.append(current_task)
            self.tasks.sort(key=lambda x: x.priority)

# Subsystem 2: Shortest Remaining Time First
class Subsystem2(threading.Thread):
    def __init__(self, tasks):
        super().__init__()
        self.tasks = sorted(tasks, key=lambda x: x.remaining_time)

    def run(self):
        while self.tasks:
            current_task = self.tasks.pop(0)
            print(f"Executing Task {current_task.task_id}")
            time.sleep(current_task.execution_time)
            print(f"Task {current_task.task_id} completed.")

# Subsystem 3: Weighted Round Robin
class Subsystem3(threading.Thread):
    def __init__(self, tasks, time_slice):
        super().__init__()
        self.tasks = tasks
        self.time_slice = time_slice

    def run(self):
        while self.tasks:
            for task in list(self.tasks):
                if task.remaining_time > 0:
                    execution_time = min(self.time_slice, task.remaining_time)
                    print(f"Executing Task {task.task_id} for {execution_time} units.")
                    time.sleep(execution_time)
                    task.remaining_time -= execution_time
                    if task.remaining_time <= 0:
                        print(f"Task {task.task_id} completed.")
                        self.tasks.remove(task)

# Example Usage
if __name__ == "__main__":
    time_unit = 1

    # Define tasks for each subsystem
    tasks1 = [Task(1, 0, 4, 1), Task(2, 0, 2, 2)]
    tasks2 = [Task(3, 0, 6), Task(4, 0, 3)]
    tasks3 = [Task(5, 0, 7), Task(6, 0, 5)]

    # Initialize subsystems
    subsystem1 = Subsystem1(tasks1, time_unit)
    subsystem2 = Subsystem2(tasks2)
    subsystem3 = Subsystem3(tasks3, time_slice=2)

    # Start subsystems
    subsystem1.start()
    subsystem2.start()
    subsystem3.start()

    # Wait for all subsystems to complete
    subsystem1.join()
    subsystem2.join()
    subsystem3.join()

    print("All tasks completed.")
