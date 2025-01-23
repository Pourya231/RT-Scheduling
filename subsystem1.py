import threading
import queue
import random


class TaskSubsystem1:
    def __init__(self, create_task_data):
        self.task_id = create_task_data[0]
        self.burst_time = create_task_data[1]
        self.resource1_usage = create_task_data[2]
        self.resource2_usage = create_task_data[3]
        self.arrival_time = create_task_data[4]
        self.target_process = create_task_data[5]
        self.state = "Ready"
        self.priority = 10  # Initial high priority, can be modified as needed.

    def __repr__(self):
        return f"Task {self.task_id} (burst_time={self.burst_time}, priority={self.priority})"


class Processor(threading.Thread):
    def __init__(self, id, subsystem, task_queue, base_quantum_time):
        super().__init__()
        self.id = id
        self.subsystem = subsystem  
        self.task_queue = task_queue
        self.base_quantum_time = base_quantum_time
        self.running_task = None
        self.running_task_quantom = 0

    def run(self):
        self.run_for_one_second()
        
    def run_for_one_second(self):
        if self.running_task is None:
            # Check for higher priority tasks in the waiting queue first
            if not self.task_queue.empty():
                task = self.task_queue.get()
                self.allocate_task(task)
            else:
                self.check_waiting_queue()
        else:
            # Existing task execution logic remains unchanged
            self.running_task_quantom -= 1
            self.running_task.burst_time -= 1

            print(
                f"Processor {self.id}: Running {self.running_task}, remaining quantum {self.running_task_quantom}"
            )

            if self.running_task.burst_time <= 0:
                print(
                    f"Task {self.running_task.task_id} has completed execution."
                )
                self.subsystem.finished_tasks.append(self.running_task)
                self.subsystem.resource1 += self.running_task.resource1_usage
                self.subsystem.resource2 += self.running_task.resource2_usage
                self.running_task = None
            elif self.running_task_quantom <= 0:
                self.task_queue.put(self.running_task)
                print(
                    f"Processor {self.id}: Quantum expired for {self.running_task}, re-queuing."
                )
                self.subsystem.resource1 += self.running_task.resource1_usage
                self.subsystem.resource2 += self.running_task.resource2_usage
                self.running_task = None

    def check_waiting_queue(self):
        with self.subsystem.waiting_queue_lock:
            highest_priority_task = None
            if not self.subsystem.waiting_queue.empty():
                # Peek into waiting queue and find the task with the highest priority
                while not self.subsystem.waiting_queue.empty():
                    task = self.subsystem.waiting_queue.get()
                    # Choose the task with the highest priority (lowest value)
                    if highest_priority_task is None or task.priority < highest_priority_task.priority:
                        if highest_priority_task is not None:
                            self.subsystem.waiting_queue.put(highest_priority_task)  # Reinsert the previous highest
                        highest_priority_task = task
                    else:
                        self.subsystem.waiting_queue.put(task)  # Reinsert if not the highest

            if highest_priority_task:
                self.allocate_task(highest_priority_task)

    def allocate_task(self, task):
        """Allocate a task to the processor if resources are available."""
        if (self.subsystem.resource1 >= task.resource1_usage and
                self.subsystem.resource2 >= task.resource2_usage):

            self.subsystem.resource1 -= task.resource1_usage
            self.subsystem.resource2 -= task.resource2_usage
            weight = max(1, int(task.burst_time * 0.75 // 1))
            self.running_task_quantom = weight

            print(
                f"Processor {self.id}: Starting {task} with quantum {self.running_task_quantom}"
            )
            
            task.state = "Running"
            task.burst_time -= 1
            self.running_task = task
        else:
            self.subsystem.waiting_queue.put(task)
            task.state = "Waiting"
            print(
                f"Processor {self.id}: Insufficient resources for {task}, moving to waiting queue."
            )

    def report_status(self):
        if self.running_task:
            print(
                f"[Report] Processor {self.id}: Running task {self.running_task.task_id}, "
                f"burst_time={self.running_task.burst_time}, quantum_remaining={self.running_task_quantom}"
            )
        else:
            print(f"[Report] Processor {self.id}: Idle, no running task.")


class Subsystem1(threading.Thread):
    def __init__(self, resource1, resource2):
        super().__init__()
        self.subsystem_id = 1
        self.processor_number = 3
        self.ready_queues = {
            i: queue.Queue() for i in range(1, self.processor_number + 1)
        }
        self.waiting_queue = queue.PriorityQueue()
        
        self.waiting_queue_lock = threading.Lock()
        self.resource1 = resource1
        self.resource2 = resource2
        self.all_resource1 = resource1
        self.all_resource2 = resource2
        self.all_tasks = []
        self.base_quantum_time = 1
        self.processors = []
        self.finished_tasks = []

    def add_task(self, task):
        self.all_tasks.append(task)

    def initial_processor(self):
        """Initialize processors only once."""
        for i in range(1, self.processor_number + 1):
            processor = Processor(
                i,
                self,
                self.ready_queues[i],
                self.base_quantum_time,
            )
            self.processors.append(processor)

    def clock_processor(self, iterations):
        """Run each processor's run_for_one_second method in parallel for the specified number of iterations."""
        for time in range(1, iterations):
            print(f"Time {time}")
            threads = []

            if time % 3 == 0:
                self.balance_load_between_processors()
                
            # Decrease priority of tasks in the waiting queue
            with self.waiting_queue_lock:  # Lock the waiting queue for thread safety
                # Create a temporary list to store tasks while we iterate
                temp_tasks = []
                while not self.waiting_queue.empty():
                    task = self.waiting_queue.get()
                    # Decrease the priority (ensure it doesn't go below zero)
                    task.priority = max(0, task.priority - 1)
                    temp_tasks.append(task)  # Store modified task
                # Re-insert tasks back into the queue
                for task in temp_tasks:
                    self.waiting_queue.put(task)

            for processor in self.processors:
                thread = threading.Thread(target=processor.run_for_one_second)
                threads.append(thread)
                thread.start()

            # Add new tasks to the ready queue based on arrival time
            for i in range(len(self.all_tasks)):
                if self.all_tasks[i].arrival_time == time:
                    self.processors[self.all_tasks[i].target_process - 1].task_queue.put(
                        self.all_tasks[i])
                    print(f"{self.all_tasks[i]} added at {time}")

            self.display(time)

            for thread in threads:
                thread.join()
                
    def get_min_max_ready_queues(self):
        """Return the processors with the minimum and maximum ready queue sizes."""
        min_processor = None
        max_processor = None
        
        if not self.processors:
            return None, None  # If there are no processors

        min_queue_size = float('inf')
        max_queue_size = -float('inf')
        
        for processor in self.processors:
            queue_size = processor.task_queue.qsize()
            if queue_size < min_queue_size:
                min_queue_size = queue_size
                min_processor = processor
            if queue_size > max_queue_size:
                max_queue_size = queue_size
                max_processor = processor

        return min_processor, max_processor

    def balance_load_between_processors(self):
        """Move a task from the max queue processor to the min queue processor if applicable."""
        min_processor, max_processor = self.get_min_max_ready_queues()
        
        if min_processor and max_processor and max_processor.task_queue.qsize() > 0:
            # Move one task from the max processor to the min processor
            task_to_move = max_processor.task_queue.get()
            min_processor.task_queue.put(task_to_move)
            print(f"Moved {task_to_move} from Processor {max_processor.id} to Processor {min_processor.id}")

    def display(self, time):
        lines = []
        line_1 = f"Time : {time}"
        lines.append(line_1)

        line_2 = f"Resources R1(Available: {self.resource1}, All: {self.all_resource1}) R2(Available: {self.resource2}, All: {self.all_resource2})"
        lines.append(line_2)

        finished_tasks = []
        for task in self.finished_tasks:
            finished_tasks.append(str(task))
        lines.append(f"  Finished tasks: {', '.join(finished_tasks)}")

        for i in range(len(self.processors)):
            line_3 = f"Core {i + 1}"
            running_task = self.processors[i].running_task
            ready_queue_size = self.processors[i].task_queue.qsize()
            tasks_in_queue = []

            task_queue = self.processors[i].task_queue
            temp_tasks = []

            while not task_queue.empty():
                task = task_queue.get()
                tasks_in_queue.append(str(task))
                temp_tasks.append(task)

            for task in temp_tasks:
                task_queue.put(task)

            lines.append(line_3)
            lines.append(f"  Running Task: {running_task}")
            lines.append(f"  Ready Queue Size: {ready_queue_size}")
            lines.append(f"  Tasks in Ready Queue: {', '.join(tasks_in_queue)}")
        
        with open("subsystem1.txt", "a") as file:
            for line in lines:
                file.write(line + "\n")


# Initialize the subsystem and tasks
subsystem1 = Subsystem1(3, 3)
subsystem1.add_task(TaskSubsystem1(["T71", 8, 2, 2, 11, 1]))
subsystem1.add_task(TaskSubsystem1(["T21", 10, 3, 3, 12, 1]))
subsystem1.add_task(TaskSubsystem1(["T91", 20, 1, 1, 12, 1]))

subsystem1.initial_processor()
subsystem1.clock_processor(60)