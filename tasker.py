import os
import sys
import tkinter as tk
from tkinter import messagebox
import win32com.client

class TaskSchedulerApp:
    def __init__(self, master):
        self.master = master
        master.title("Task Scheduler")

        self.task_name_label = tk.Label(master, text="Task Name:")
        self.task_name_label.pack()

        self.task_name_entry = tk.Entry(master)
        self.task_name_entry.pack()

        self.schedule_label = tk.Label(master, text="Schedule (HH:MM):")
        self.schedule_label.pack()

        self.schedule_frame = tk.Frame(master)
        self.schedule_frame.pack()

        self.hour_entry = tk.Entry(self.schedule_frame, width=2)
        self.hour_entry.grid(row=0, column=0)
        self.hour_label = tk.Label(self.schedule_frame, text=":")
        self.hour_label.grid(row=0, column=1)
        self.minute_entry = tk.Entry(self.schedule_frame, width=2)
        self.minute_entry.grid(row=0, column=2)

        self.create_task_button = tk.Button(master, text="Create Task", command=self.create_task)
        self.create_task_button.pack()

        self.delete_task_button = tk.Button(master, text="Delete Task", command=self.delete_task)
        self.delete_task_button.pack()

    def create_task(self):
        task_name = self.task_name_entry.get()
        hour = self.hour_entry.get()
        minute = self.minute_entry.get()

        if not task_name or not hour or not minute:
            messagebox.showwarning("Warning", "Task name and schedule cannot be empty.")
            return

        schedule_time = f"2024-03-12T{hour.zfill(2)}:{minute.zfill(2)}:00"
        script_path = os.path.abspath("c:/Users/ahmet/Desktop/driveBackup/setup.py")  # Update with your script path

        create_daily_task(task_name, script_path, schedule_time)
        messagebox.showinfo("Success", "Task has been created successfully.")

    def delete_task(self):
        task_name = self.task_name_entry.get()

        if not task_name:
            messagebox.showwarning("Warning", "Task name cannot be empty.")
            return

        delete_task(task_name)
        messagebox.showinfo("Success", "Task has been deleted successfully.")

def create_daily_task(task_name, script_path, start_time):
    scheduler = win32com.client.Dispatch('Schedule.Service')
    scheduler.Connect()

    root_folder = scheduler.GetFolder('\\')
    task_def = scheduler.NewTask(0)
    task_def.RegistrationInfo.Description = task_name

    triggers = task_def.Triggers
    trigger = triggers.Create(1)  # 1 means 'on a schedule'
    trigger.StartBoundary = start_time

    action = task_def.Actions.Create(0)  # 0 means 'execute a program'
    action.Path = sys.executable  # Use Python interpreter path
    action.Arguments = script_path  # Pass script path as argument

    root_folder.RegisterTaskDefinition(
        task_name, task_def, 6, None, None, 3)  # 6 means 'update if exists'

def delete_task(task_name):
    scheduler = win32com.client.Dispatch('Schedule.Service')
    scheduler.Connect()

    root_folder = scheduler.GetFolder('\\')
    try:
        root_folder.DeleteTask(task_name, 0)  # 0 means 'unregister'
        print(f"Task '{task_name}' has been deleted successfully.")
    except Exception as e:
        print(f"An error occurred while deleting task '{task_name}': {e}")

if __name__ == "__main__":
    root = tk.Tk()
    app = TaskSchedulerApp(root)
    root.mainloop()
