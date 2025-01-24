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
            # Check for task preemption
            if self.running_task and self.running_task.remaining_time > 0:
                if not self.subsystem.ready_queue.empty():
                    # Peek at the next task in the queue
                    next_task = self.subsystem.ready_queue.queue[0]  # Get the highest priority task without removing it
                    if next_task.remaining_time < self.running_task.remaining_time:
                        # Preempt current task
                        print(f"Subsystem {self.subsystem.subsystem_id} Processor {self.id}: Preempting {self.running_task} for {next_task}")

                        # Put the current task back to the queue
                        self.subsystem.ready_queue.put(self.running_task)
                        self.running_task = None  # Clear the current running task

            # If there's a running task and it still has remaining time, continue it
            if self.running_task:
                self.running_task.remaining_time -= 1
                print(
                    f"Subsystem {self.subsystem.subsystem_id} Processor {self.id}: Running {self.running_task}, remaining time {self.running_task.remaining_time}"
                )
                # Update tasks_report
                task_id = self.running_task.task_id
                self.subsystem.tasks_report[task_id]['running_processors'].append(self.id)

                if self.running_task.remaining_time <= 0:
                    print(
                        f"Subsystem {self.subsystem.subsystem_id} Task {self.running_task.task_id} has completed execution."
                    )
                    self.subsystem.finished_tasks.append(self.running_task)
                    self.subsystem.tasks_report[task_id]['finish_time'] = self.subsystem.current_time
                    self.release_resources()
                    self.running_task = None

            # Process the next task from the queue
            elif not self.subsystem.ready_queue.empty():
                task = self.subsystem.ready_queue.get()
                if self.can_allocate(task):
                    self.allocate_task(task)
                else:
                    if (self.subsystem.all_resource1 < task.resource1_usage or self.subsystem.all_resource2 < task.resource2_usage):
                        print(
                            f"Subsystem {self.subsystem.subsystem_id} Processor {self.id}: All resources for task {task} is not enough. Not run this task"
                        )
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
        print(f"Subsystem {self.subsystem.subsystem_id} Processor {self.id}: Allocating task {task}")

        # Release resources of current task if any
        self.release_resources()
        
        self.subsystem.resource1 -= task.resource1_usage
        self.subsystem.resource2 -= task.resource2_usage

        print(
            f"Subsystem {self.subsystem.subsystem_id} Processor {self.id}: Starting {task}"
        )

        self.running_task = task
        self.running_task.remaining_time -= 1

        # Update tasks_report with the running processor
        task_id = task.task_id
        self.subsystem.tasks_report[task_id]['running_processors'].append(self.id)

        print(
            f"Subsystem {self.subsystem.subsystem_id} Processor {self.id}: Running {self.running_task}, remaining time {self.running_task.remaining_time}"
        )

        if self.running_task.remaining_time <= 0:
            print(
                f"Subsystem {self.subsystem.subsystem_id} Task {self.running_task.task_id} has completed execution."
            )
            self.subsystem.finished_tasks.append(self.running_task)
            self.subsystem.tasks_report[task_id]['finish_time'] = self.subsystem.current_time
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
        self.tasks_report = {}
        self.ready_queue_lock = threading.Lock()  # Lock for the ready queue
        self.current_time = 0

    def add_task(self, task):
        self.all_tasks.append(task)
        self.tasks_report[task.task_id] = {
            'arrival_time': task.arrival_time,
            'finish_time': None,
            'running_processors': [],
            'running_subsystem': 'Subsystem 1'
        }

    def initial_processors(self):
        """Initialize processors."""
        for i in range(2):  # Two processors
            processor = Processor(i + 1, self)
            self.processors.append(processor)

    def clock_processor(self, time):
        """Run each processor's run_for_one_second method in parallel."""
        # print(f"Time {time}")
        self.current_time = time
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
                
    def save_tasks_result(self):
        """Save the results of the tasks to a text file."""
        with open("tasks_results_subsystem2.txt", "w") as file:
            file.write(f"Results of tasks in Subsystem {self.subsystem_id}:\n")
            file.write(f"{'Task ID':<10} {'Arrival Time':<15} {'Finish Time':<15} {'Running Processors'}\n")
            file.write('-' * 70 + '\n')
            
            for task_id, report in self.tasks_report.items():
                arrival_time = report['arrival_time']
                finish_time = report['finish_time'] if report['finish_time'] is not None else 'Not Completed'
                running_processors = ', '.join(map(str, report['running_processors']))
                
                file.write(f"{task_id:<10} {arrival_time:<15} {finish_time:<15} {running_processors}\n")
                
            print(f"Results saved to tasks_results.txt")
        


# Create subsystem and add tasks
subsystem = Subsystem2(3, 3)
subsystem.add_task(TaskSubsystem2(["T1", 7, 1, 1, 1]))
subsystem.add_task(TaskSubsystem2(["T2", 6, 2, 1, 3]))
subsystem.add_task(TaskSubsystem2(["T3", 2, 1, 1, 4]))

# Start processors
subsystem.initial_processors()
subsystem.clock_processor(30)
