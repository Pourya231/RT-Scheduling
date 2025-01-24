import threading
from subsystem1 import Subsystem1
from subsystem2 import Subsystem2
from subsystem3 import Subsystem3
from subsystem3 import TaskSubsystem3

class MainSubsystem:
    def __init__(self, subsystems):
        self.subsystems = subsystems
        self.global_time = 0
        self.max_time = max([getattr(subsystem, 'max_time', 0) for subsystem in subsystems])
        self.time_lock = threading.Lock()

    def synchronize_subsystems(self):
        """Ensure all subsystems process one time unit together."""
        threads = []

        for subsystem in self.subsystems:
            thread = threading.Thread(target=subsystem.run_one_time_unit)
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

    def run(self):
        while self.global_time < self.max_time:
            print(f"[MainSubsystem] Global Time: {self.global_time}")
            with self.time_lock:
                self.synchronize_subsystems()
                self.global_time += 1


# Add run_one_time_unit method to all subsystems
class UpdatedSubsystem1(Subsystem1):
    def run_one_time_unit(self):
        if not hasattr(self, 'time'):
            self.time = 0
        if self.time < getattr(self, 'max_time', 50):
            print(f"[Subsystem1] Time: {self.time}")
            for processor in self.processors:
                processor.run_for_one_second()
            self.time += 1

class UpdatedSubsystem2(Subsystem2):
    def run_one_time_unit(self):
        if not hasattr(self, 'time'):
            self.time = 0
        if self.time < getattr(self, 'max_time', 50):
            print(f"[Subsystem2] Time: {self.time}")
            for processor in self.processors:
                processor.run_for_one_second()
            self.time += 1

class UpdatedSubsystem3(Subsystem3):
    def run_one_time_unit(self):
        if not hasattr(self, 'time'):
            self.time = 0
        if self.time < getattr(self, 'max_time', 50):
            print(f"[Subsystem3] Time: {self.time}")
            for processor in self.processors:
                processor.run_for_one_time_unit()
            self.time += 1

# Main function
if __name__ == "__main__":
    subsystem1 = UpdatedSubsystem1(10, 10)
    subsystem1.add_task(["T1", 8, 1, 1, 0, 1])
    subsystem1.add_task(["T2", 12, 2, 1, 0, 2])
    subsystem1.add_task(["T3", 10, 1, 1, 2, 3])
    subsystem1.initial_processor()

    subsystem2 = UpdatedSubsystem2(10, 10)
    subsystem2.add_task(["T4", 6, 1, 1, 1])
    subsystem2.add_task(["T5", 7, 2, 1, 2])
    subsystem2.add_task(["T6", 9, 1, 1, 3])
    subsystem2.initial_processors()

    subsystem3 = UpdatedSubsystem3(max_time=50, subsystem1=subsystem1, subsystem2=subsystem2)
    subsystem3.add_task(TaskSubsystem3("T7", period=10, execution_time=3, deadline=10))
    subsystem3.add_task(TaskSubsystem3("T8", period=15, execution_time=4, deadline=15))
    subsystem3.add_task(TaskSubsystem3("T9", period=20, execution_time=5, deadline=20))
    subsystem3.initialize_processors(num_processors=1)

    main_subsystem = MainSubsystem([subsystem1, subsystem2, subsystem3])
    main_subsystem.run()