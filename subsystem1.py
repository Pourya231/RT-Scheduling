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
            # Check for preemption
            self.check_preemption()

            # Execute the current task
            if self.running_task:
                self.running_task_quantom -= 1
                self.running_task.burst_time = max(0, self.running_task.burst_time - 1)

                print(
                    f"Subsystem {self.subsystem.subsystem_id} Processor {self.id}: Running {self.running_task}, remaining quantum {self.running_task_quantom}"
                )

                if self.running_task.burst_time == 0:
                    print(
                        f"Subsystem {self.subsystem.subsystem_id} Task {self.running_task.task_id} has completed execution."
                    )
                    self.subsystem.tasks_report[self.running_task.task_id]['finish_time'] = self.subsystem.current_time
                    self.subsystem.finished_tasks.append(self.running_task)
                    self.subsystem.resource1 += self.running_task.resource1_usage
                    self.subsystem.resource2 += self.running_task.resource2_usage
                    self.running_task = None  # Clear the current task
                elif self.running_task_quantom <= 0:
                    # Instead of re-queuing, manage the case properly:
                    print(
                        f"Subsystem {self.subsystem.subsystem_id} Processor {self.id}: Quantum expired for {self.running_task}"
                    )
                    self.subsystem.resource1 += self.running_task.resource1_usage
                    self.subsystem.resource2 += self.running_task.resource2_usage
                    # Only if you want to queue it back if it didn't finish
                    self.running_task.state = "Waiting"
                    self.task_queue.put(self.running_task)
                    self.running_task = None  # Clear the current task

    def check_preemption(self):
        """Check for higher-priority tasks in the ready queue and preempt if necessary."""
        # Check the ready queue for a higher-priority task
        if not self.task_queue.empty():
            # Peek at the highest-priority task in the ready queue
            top_ready_task = self.task_queue.queue[0]
            
            # If the top task in the ready queue has higher priority than the running task, preempt
            if self.running_task and top_ready_task < self.running_task:
                print(
                    f"Subsystem {self.subsystem.subsystem_id} Processor {self.id}: Preempting {self.running_task} for higher-priority task {top_ready_task}"
                )
                
                # Move the current running task back to the ready queue
                self.running_task.state = "Waiting"
                self.task_queue.put(self.running_task)
                
                # Release resources used by the preempted task
                self.subsystem.resource1 += self.running_task.resource1_usage
                self.subsystem.resource2 += self.running_task.resource2_usage
                
                # Clear the running task
                self.running_task = None

                # Allocate the higher-priority task
                self.allocate_task(top_ready_task)

    def allocate_task(self, task):
        """Allocate a task to the processor if resources are available."""
        if (self.subsystem.resource1 >= task.resource1_usage and
                self.subsystem.resource2 >= task.resource2_usage):

            self.subsystem.resource1 -= task.resource1_usage
            self.subsystem.resource2 -= task.resource2_usage
            weight = max(1, int(task.burst_time * 0.75 // 1))
            self.running_task_quantom = weight

            print(
                f"Subsystem {self.subsystem.subsystem_id} Processor {self.id}: Starting {task} with quantum {self.running_task_quantom}"
            )

            self.subsystem.tasks_report[task.task_id]['running_processors'].append(self.id)
            task.state = "Running"
            task.priority =10
            self.running_task = task
        else:
            if (self.subsystem.all_resource1 < task.resource1_usage or self.subsystem.all_resource2 < task.resource2_usage):
                print(
                    f"Subsystem {self.subsystem.subsystem_id} Processor {self.id}: All resources for task {task} is not enough. Not run this task"
                )
            else:
                with self.subsystem.waiting_queue_lock:  # Ensure thread-safe access to the waiting queue
                    self.subsystem.waiting_queue.put(task)
                    task.state = "Waiting"
                    print(
                        f"Subsystem {self.subsystem.subsystem_id} Processor {self.id}: Insufficient resources for {task}, moving to waiting queue."
                    )
                    # Debug print
                    print(
                        f"Subsystem {self.subsystem.subsystem_id} Waiting queue size: {self.subsystem.waiting_queue.qsize()}")


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
        self.tasks_report = {}
        self.current_time = 0

    def add_task(self, task):
        self.all_tasks.append(task)
        self.tasks_report[task.task_id] = {
            'arrival_time': task.arrival_time,
            'finish_time': None,
            'time_in_waiting_queue': 0,
            'running_processors': [],
            'running_subsystem': 'Subsystem 1'
        }

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

    def clock_processor(self, time):
        self.current_time = time
        print(f"Time {time}")
        threads = []

        # Dispatch tasks from waiting queue every 5 cycles
        if self.current_time % 3 == 0:  # Every 20 cycles, force dispatch one task
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
                self.tasks_report[task.task_id]['time_in_waiting_queue'] += 1
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
                target_processor = min(self.processors, key=lambda p: p.task_queue.qsize())

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
    
    def save_tasks_result(self):
        """Save the results of the tasks to a text file."""
        with open("tasks_results_subsystem1.txt", "w") as file:
            file.write(f"Results of tasks in Subsystem {self.subsystem_id}:\n")
            file.write(f"{'Task ID':<10} {'Arrival Time':<15} {'Finish Time':<15} {'Time in Waiting':<20} {'Running Processors'}\n")
            file.write('-' * 85 + '\n')
            
            for task_id, report in self.tasks_report.items():
                arrival_time = report['arrival_time']
                finish_time = report['finish_time'] if report['finish_time'] is not None else 'Not Completed'
                time_in_waiting = report['time_in_waiting_queue'] if report['time_in_waiting_queue'] is not None else 0
                running_processors = ', '.join(map(str, report['running_processors']))

                file.write(f"{task_id:<10} {arrival_time:<15} {finish_time:<15} {time_in_waiting:<20} {running_processors}\n")

            print(f"Results saved to tasks_results_subsystem1.txt")

# Initialize the subsystem and tasks
subsystem1 = Subsystem1(3, 3)
subsystem1.add_task(TaskSubsystem1(["T1", 8, 1, 1, 0, 1]))
subsystem1.add_task(TaskSubsystem1(["T2", 12, 2, 2, 1, 2]))
subsystem1.add_task(TaskSubsystem1(["T3", 10, 1, 1, 2, 3]))

subsystem1.initial_processor()
for i in range(50):
    subsystem1.clock_processor(i)

subsystem1.save_tasks_result()

