import threading
import time
import heapq

# تعریف وضعیت‌های وظیفه
READY = "Ready"
WAITING = "Waiting"
RUNNING = "Running"
DEADLOCK = "Deadlock"

# کلاس وظیفه
class Task:
    def __init__(self, name, execution_time, deadline, required_resources):
        self.name = name
        self.execution_time = execution_time
        self.deadline = deadline
        self.required_resources = required_resources
        self.state = WAITING
        self.time_remaining = execution_time
        self.arrival_time = time.time()

    def execute(self):
        self.state = RUNNING
        print(f"Executing {self.name} for {self.time_remaining} seconds.")
        time.sleep(self.time_remaining)
        self.state = READY
        print(f"{self.name} has finished execution.")
        self.time_remaining = 0  # Task completed

# زیرسیستم دوم (Shortest Time Remaining)
class SubSystem2:
    def __init__(self, resources_r1, resources_r2):
        self.resources_r1 = resources_r1
        self.resources_r2 = resources_r2
        self.ready_queue = []
        self.processors = [None, None]  # دو هسته پردازشی

    def add_task(self, task):
        heapq.heappush(self.ready_queue, (task.time_remaining, task))  # استفاده از heap برای SJF

    def schedule_tasks(self):
        for i in range(len(self.processors)):
            if self.processors[i] is None and self.ready_queue:
                _, task = heapq.heappop(self.ready_queue)
                if self.resources_r1 >= task.required_resources[0] and self.resources_r2 >= task.required_resources[1]:
                    self.processors[i] = task
                    task.execute()
                    self.processors[i] = None
                    self.allocate_resources(task)
                else:
                    print(f"Task {task.name} is waiting due to insufficient resources.")
                    task.state = WAITING
                    self.add_task(task)  # دوباره به صف آماده برمی‌گردد

    def allocate_resources(self, task):
        self.resources_r1 -= task.required_resources[0]
        self.resources_r2 -= task.required_resources[1]
        print(f"Resources allocated for {task.name}. Remaining: R1={self.resources_r1}, R2={self.resources_r2}")

# زیرسیستم سوم (Real-Time)
class SubSystem3:
    def __init__(self, resources_r1, resources_r2):
        self.resources_r1 = resources_r1
        self.resources_r2 = resources_r2
        self.ready_queue = []
        self.waiting_queue = []
        self.processors = [None]  # یک هسته پردازشی

    def add_task(self, task):
        if task.deadline >= time.time():
            self.ready_queue.append(task)
        else:
            print(f"Task {task.name} missed the deadline.")
            task.state = DEADLOCK

    def schedule_tasks(self):
        for task in self.ready_queue:
            if self.resources_r1 >= task.required_resources[0] and self.resources_r2 >= task.required_resources[1]:
                self.process_task(task)
            else:
                print(f"Task {task.name} is waiting for resources.")
                self.waiting_queue.append(task)

    def process_task(self, task):
        if task.time_remaining > 2:
            task.time_remaining -= 2
            print(f"Executing {task.name} in chunks (2 time units). Remaining time: {task.time_remaining}")
        else:
            print(f"Executing final chunk of {task.name}.")
            task.time_remaining = 0  # Task complete

# کلاس نخ اصلی
class MainThread:
    def __init__(self):
        self.subsystems = []

    def add_subsystem(self, subsystem):
        self.subsystems.append(subsystem)

    def start_system(self):
        while True:
            for subsystem in self.subsystems:
                subsystem.schedule_tasks()
            time.sleep(1)  # هر ثانیه یکبار چک کردن وضعیت زیرسیستم‌ها

# ایجاد وظایف
task1 = Task("Task1", 3, time.time() + 10, [1, 1])  # وظیفه‌ای که 3 ثانیه طول می‌کشد
task2 = Task("Task2", 4, time.time() + 12, [2, 1])  # وظیفه‌ای که 4 ثانیه طول می‌کشد

# زیرسیستم‌ها
subsystem2 = SubSystem2(5, 5)
subsystem2.add_task(task1)
subsystem2.add_task(task2)

subsystem3 = SubSystem3(3, 3)
subsystem3.add_task(task1)
subsystem3.add_task(task2)

# ایجاد نخ اصلی
main_thread = MainThread()
main_thread.add_subsystem(subsystem2)
main_thread.add_subsystem(subsystem3)

# اجرای سیستم
main_thread.start_system()
