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
        # Initial high priority (lower value is higher priority).
        self.priority = 10

    def __repr__(self):
        return f"Task {self.task_id} (burst_time={self.burst_time}, priority={self.priority})"

    def __lt__(self, other):
        """Comparison method for PriorityQueue (lower priority value means higher priority)."""
        return self.priority < other.priority


class Processor(threading.Thread):
    def __init__(self, id, subsystem, task_queue, base_quantum_time):
        super().__init__()
        self.id = id
        self.subsystem = subsystem
        self.task_queue = task_queue
        self.base_quantum_time = base_quantum_time
        self.running_task = None
        self.running_task_quantom = 0

    def run_for_one_second(self):
        if self.running_task is None:
            if not self.task_queue.empty():
                task = self.task_queue.get()
                self.allocate_task(task)
        else:
            # Check if there is a higher-priority task in the task_queue or waiting_queue
            self.check_preemption()

            # Execute the current task
            if self.running_task:
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

    def check_preemption(self):
        """Check for higher-priority tasks and preempt if necessary."""
        higher_priority_task = None

        # Check the ready queue for a higher-priority task
        if not self.task_queue.empty():
            # Peek at the highest-priority task
            top_ready_task = self.task_queue.queue[0]
            if top_ready_task < self.running_task:  # Compare priorities
                higher_priority_task = self.task_queue.get()

        # Check the waiting queue for a higher-priority task
        with self.subsystem.waiting_queue_lock:
            if not self.subsystem.waiting_queue.empty():
                waiting_tasks = []
                while not self.subsystem.waiting_queue.empty():
                    task = self.subsystem.waiting_queue.get()
                    if higher_priority_task is None or task < higher_priority_task:
                        if higher_priority_task:
                            self.subsystem.waiting_queue.put(
                                higher_priority_task)
                        higher_priority_task = task
                    else:
                        waiting_tasks.append(task)

                # Reinsert remaining tasks into the waiting queue
                for task in waiting_tasks:
                    self.subsystem.waiting_queue.put(task)

        # Preempt the current running task if necessary
        if higher_priority_task and self.running_task and higher_priority_task < self.running_task:
            print(
                f"Processor {self.id}: Preempting {self.running_task} for higher-priority task {higher_priority_task}"
            )
            self.running_task.state = "Waiting"
            self.task_queue.put(self.running_task)
            self.subsystem.resource1 += self.running_task.resource1_usage
            self.subsystem.resource2 += self.running_task.resource2_usage

            # Allocate the higher-priority task
            self.allocate_task(higher_priority_task)

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
            with self.subsystem.waiting_queue_lock:  # Ensure thread-safe access to the waiting queue
                self.subsystem.waiting_queue.put(task)
                task.state = "Waiting"
                print(
                    f"Processor {self.id}: Insufficient resources for {task}, moving to waiting queue."
                )
                # Debug print
                print(
                    f"Waiting queue size: {self.subsystem.waiting_queue.qsize()}")

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
        for time in range(1, iterations + 1):
            print(f"Time {time}")
            threads = []

            # Dispatch tasks from waiting queue every 5 cycles
            if time % 10 == 0:
                self.dispatch_tasks_to_ready_queue()

            # Call load balancing every 3 cycles
            if time % 5 == 0:
                self.balance_load_between_processors()

            # Decrease priority of tasks in the waiting queue
            with self.waiting_queue_lock:  # Lock the waiting queue for thread safety
                temp_tasks = []
                while not self.waiting_queue.empty():
                    task = self.waiting_queue.get()
                    # Decrease priority
                    task.priority = max(0, task.priority - 1)
                    temp_tasks.append(task)
                for task in temp_tasks:
                    self.waiting_queue.put(task)

            # Execute each processor's run logic
            for processor in self.processors:
                thread = threading.Thread(target=processor.run_for_one_second)
                threads.append(thread)
                thread.start()

            # Add new tasks to the ready queue based on arrival time
            for task in self.all_tasks:
                if task.arrival_time == time:
                    self.processors[task.target_process -
                                    1].task_queue.put(task)
                    print(f"{task} added at {time}")

            # Display subsystem status
            self.display(time)

            for thread in threads:
                thread.join()

    def dispatch_tasks_to_ready_queue(self):
        # Debug print
        self.print_waiting_queue()
        print(
            f"Waiting queue size before dispatch: {self.waiting_queue.qsize()}")
        """Move one task from the waiting queue to the ready queues of processors every 5 cycles."""
        with self.waiting_queue_lock:  # Ensure thread safety
            if not self.waiting_queue.empty():
                # Get the highest-priority task from the waiting queue
                task = self.waiting_queue.get()
                print(f"Found task {task} in waiting queue.")  # Debug print

                # Find a random processor to assign the task to
                # Correct usage of random.choice
                target_processor = random.choice(self.processors)

                # Add the task to the target processor's ready queue
                target_processor.task_queue.put(task)
                print(
                    f"Dispatched {task} from waiting queue to Processor {target_processor.id}"
                )
    def print_waiting_queue(self):
        """Print all tasks in the waiting queue."""
        with self.waiting_queue_lock:  # Ensure thread-safe access to the waiting queue
            if self.waiting_queue.empty():
                print("Waiting queue is empty.")
            else:
                print("Tasks in the waiting queue:")
                temp_tasks = []
                while not self.waiting_queue.empty():
                    task = self.waiting_queue.get()
                    print(task)
                    temp_tasks.append(task)
                # Reinsert tasks back into the waiting queue
                for task in temp_tasks:
                    self.waiting_queue.put(task)

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
        min_processor = None
        max_processor = None

        if not self.processors:
            return  # No processors available

        # Identify processors with minimum and maximum ready queue sizes
        min_queue_size = float('inf')
        max_queue_size = -float('inf')

        for processor in self.processors:
            queue_size = processor.task_queue.qsize()

            # Skip processors that are running a task
            if processor.running_task is None and queue_size < min_queue_size:
                min_queue_size = queue_size
                min_processor = processor

            if queue_size > max_queue_size:
                max_queue_size = queue_size
                max_processor = processor

        if min_processor and max_processor and max_processor.task_queue.qsize() > 0:
            # Move one task from the max processor to the min processor
            task_to_move = max_processor.task_queue.get()
            min_processor.task_queue.put(task_to_move)
            print(
                f"Moved {task_to_move} from Processor {max_processor.id} to Processor {min_processor.id}")

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
            lines.append(
                f"  Tasks in Ready Queue: {', '.join(tasks_in_queue)}")

        with open("subsystem1.txt", "a") as file:
            for line in lines:
                file.write(line + "\n")


# Initialize the subsystem and tasks
subsystem1 = Subsystem1(3, 3)
subsystem1.add_task(TaskSubsystem1(["T71", 8, 1, 1, 11, 1]))
subsystem1.add_task(TaskSubsystem1(["T21", 10, 2, 2, 12, 1]))
subsystem1.add_task(TaskSubsystem1(["T91", 20, 1, 1, 12, 1]))

subsystem1.initial_processor()
subsystem1.clock_processor(60)