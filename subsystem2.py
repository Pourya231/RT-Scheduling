import threading
import queue
import random


class TaskSubsystem2:
    def __init__(self, create_task_data):
        self.task_id = create_task_data[0]
        self.burst_time = create_task_data[1]
        self.resource1_usage = create_task_data[2]
        self.resource2_usage = create_task_data[3]
        self.arrival_time = create_task_data[4]
        self.remaining_time = self.burst_time  # Initialize remaining_time for SRTF

    def __repr__(self):
        return f"Task {self.task_id} (remaining_time={self.remaining_time})"

    def __lt__(self, other):
        return self.remaining_time < other.remaining_time  # For priority queue comparison


class Processor(threading.Thread):
    def __init__(self, id, subsystem):
        super().__init__()
        self.id = id
        self.subsystem = subsystem
        self.running_task = None
        self.lock = threading.Lock()

    def run(self):
        for _ in range(80):
            self.run_for_one_second()

    def run_for_one_second(self):
        with self.lock:
            if self.running_task and self.running_task.remaining_time > 0:
                # Continue running the current task
                self.running_task.remaining_time -= 1
                print(
                    f"Subsystem {self.subsystem.subsystem_id} Processor {self.id}: Running {self.running_task}, remaining time {self.running_task.remaining_time}"
                )

                if self.running_task.remaining_time <= 0:
                    print(
                        f"Subsystem {self.subsystem.subsystem_id} Task {self.running_task.task_id} has completed execution."
                    )
                    self.subsystem.finished_tasks.append(self.running_task)
                    self.release_resources()
                    self.running_task = None

            elif not self.subsystem.ready_queue.empty():
                task = self.subsystem.ready_queue.get()

                if self.can_allocate(task):
                    self.allocate_task(task)
                else:
                    # If unable to allocate, put the task back in the queue
                    with self.subsystem.ready_queue_lock:
                        self.subsystem.ready_queue.put(task)

    def can_allocate(self, task):
        """Check if resources are available to allocate the task."""
        return (
            self.subsystem.resource1 >= task.resource1_usage
            and self.subsystem.resource2 >= task.resource2_usage
        )

    def allocate_task(self, task):
        """Allocate a task to the processor if resources are available."""
        self.subsystem.resource1 -= task.resource1_usage
        self.subsystem.resource2 -= task.resource2_usage

        print(
            f"Subsystem {self.subsystem.subsystem_id} Processor {self.id}: Starting {task}"
        )

        self.running_task = task
        self.running_task.remaining_time -= 1
        print(
            f"Subsystem {self.subsystem.subsystem_id} Processor {self.id}: Running {self.running_task}, remaining time {self.running_task.remaining_time}"
        )

        if self.running_task.remaining_time <= 0:
            print(
                f"Subsystem {self.subsystem.subsystem_id} Task {self.running_task.task_id} has completed execution."
            )
            self.subsystem.finished_tasks.append(self.running_task)
            self.release_resources()
            self.running_task = None

    def release_resources(self):
        """Release resources when task execution is complete."""
        if self.running_task:
            self.subsystem.resource1 += self.running_task.resource1_usage
            self.subsystem.resource2 += self.running_task.resource2_usage



class Subsystem2(threading.Thread):
    def __init__(self, resource1, resource2):
        super().__init__()
        self.subsystem_id = 2
        self.resource1 = resource1
        self.all_resource1 = resource1
        self.resource2 = resource2
        self.all_resource2 = resource2
        self.ready_queue = queue.PriorityQueue()
        self.processors = []
        self.all_tasks = []
        self.finished_tasks = []
        self.ready_queue_lock = threading.Lock()  # Lock for the ready queue

    def add_task(self, task):
        self.all_tasks.append(task)

    def initial_processors(self):
        """Initialize processors."""
        for i in range(2):  # Two processors
            processor = Processor(i + 1, self)
            self.processors.append(processor)

    def clock_processor(self, time):
        """Run each processor's run_for_one_second method in parallel."""
        # print(f"Time {time}")
        threads = []

        for i in range(len(self.all_tasks)):
            if self.all_tasks[i].arrival_time == time:
                with self.ready_queue_lock:  # Acquire lock before accessing ready queue
                    self.ready_queue.put(self.all_tasks[i])
                print(f"{self.all_tasks[i]} added at {time}")

        for processor in self.processors:
            thread = threading.Thread(target=processor.run_for_one_second)
            threads.append(thread)
            thread.start()

        self.display(time)
        for thread in threads:
            thread.join()

    def display(self, time):
        lines = []
        line_1 = f"Time : {time}"
        lines.append(line_1)

        # Format the resources line
        line_2 = f"Resources R1(Available: {self.resource1}, All: {self.all_resource1}) R2(Available: {self.resource2}, All: {self.all_resource2})"
        lines.append(line_2)

        # Format the finished tasks line
        finished_tasks = [str(task) for task in self.finished_tasks]
        lines.append(f"finished tasks = [{', '.join(finished_tasks)}]")

        # Add the status of each core (processor)
        for i, processor in enumerate(self.processors, start=1):
            running_task = processor.running_task
            if running_task:
                lines.append(f"Core{i}:\n    Running task : {running_task}")
            else:
                lines.append(f"Core{i}:\n    Running task :")

        # Write to the file
        with open("subsystem2.txt", "a") as file:
            for line in lines:
                file.write(line + "\n")


# Create subsystem and add tasks
subsystem = Subsystem2(3, 3)
subsystem.add_task(TaskSubsystem2(["T1", 7, 1, 1, 1]))
subsystem.add_task(TaskSubsystem2(["T2", 6, 2, 1, 3]))
subsystem.add_task(TaskSubsystem2(["T3", 2, 1, 1, 4]))

# Start processors
subsystem.initial_processors()
subsystem.clock_processor(30)
