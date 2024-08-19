import tkinter as tk
from tkinter import ttk, messagebox
import requests
from datetime import datetime

API_URL = "http://localhost:5000"

class DeviceMonitoringApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Device Monitoring")

        # Treeview for displaying devices in a table
        self.device_tree = ttk.Treeview(root, columns=('Name', 'Status', 'Last Checked'), show='headings')
        self.device_tree.heading('Name', text='Name')
        self.device_tree.heading('Status', text='Status')
        self.device_tree.heading('Last Checked', text='Last Checked')
        self.device_tree.pack(fill=tk.BOTH, expand=True)

        # Add New Device (All in one line)
        self.add_device_frame = tk.Frame(root)
        self.add_device_frame.pack(pady=10, fill=tk.X)

        # Create and place the refresh button
        self.refresh_button = tk.Button(root, text="Refresh Devices", command=self.refresh_devices)
        self.refresh_button.pack(pady=10)  # Ensure it's packed or placed in the layout


        tk.Label(self.add_device_frame, text="Device Name:").grid(row=0, column=0, padx=5)
        self.new_device_name = tk.Entry(self.add_device_frame)
        self.new_device_name.grid(row=0, column=1, padx=5)

        tk.Label(self.add_device_frame, text="Status:").grid(row=0, column=2, padx=5)
        self.new_device_status = ttk.Combobox(self.add_device_frame, values=["Running", "Down", "Unknown"])
        self.new_device_status.grid(row=0, column=3, padx=5)
        self.new_device_status.current(0)  # Default to "Running"

        self.add_device_button = tk.Button(self.add_device_frame, text="Add Device", command=self.add_device)
        self.add_device_button.grid(row=0, column=4, padx=5)

        # Search Devices
        self.search_frame = tk.Frame(root)
        self.search_frame.pack(pady=10)

        tk.Label(self.search_frame, text="Search Device:").grid(row=0, column=0)
        self.search_query = tk.Entry(self.search_frame)
        self.search_query.grid(row=0, column=1)

        self.search_button = tk.Button(self.search_frame, text="Search", command=self.search_devices)
        self.search_button.grid(row=0, column=2)

        # Change Device Status
        self.change_status_frame = tk.Frame(root)
        self.change_status_frame.pack(pady=10, fill=tk.X)

        tk.Label(self.change_status_frame, text="New Status:").grid(row=0, column=0, padx=5)
        self.change_device_status = ttk.Combobox(self.change_status_frame, values=["Running", "Down", "Unknown"])
        self.change_device_status.grid(row=0, column=1, padx=5)
        self.change_device_status.current(0)  # Default to "Running"

        self.change_status_button = tk.Button(self.change_status_frame, text="Change Status", command=self.change_device_status_func)
        self.change_status_button.grid(row=0, column=2, padx=5)

        # Delete Device Button
        self.delete_device_button = tk.Button(root, text="Delete Selected Device", command=self.delete_device)
        self.delete_device_button.pack(pady=10)

        self.refresh_devices()

    def refresh_devices(self):
        try:
            response = requests.get(f"{API_URL}/devices", timeout=10)  # Set a timeout for the request
            response.raise_for_status()  # Raise an exception for HTTP error responses
            devices = response.json()
            self.device_tree.delete(*self.device_tree.get_children())  # Clear existing data
            for device_id, device_info in devices.items():
                # Parse and format the date consistently
                last_checked = self.parse_date(device_info['last_checked'])
                self.device_tree.insert("", "end", values=(
                    device_id,
                    device_info['status'],
                    last_checked.strftime("%Y-%m-%d %H:%M:%S")
                ))
        except requests.exceptions.HTTPError as http_err:
            messagebox.showerror("Error", f"HTTP error occurred: {http_err}")
        except requests.exceptions.RequestException as req_err:
            messagebox.showerror("Error", f"Error during request: {req_err}")
        except Exception as e:
            messagebox.showerror("Error", f"An unexpected error occurred: {e}")

    def add_device(self):
        device_name = self.new_device_name.get()
        status = self.new_device_status.get()

        if not device_name or not status:
            messagebox.showwarning("Input Error", "Please enter both device name and status.")
            return

        response = requests.post(f"{API_URL}/device", json={'name': device_name, 'status': status})
        if response.status_code == 201:
            messagebox.showinfo("Success", "Device added successfully!")
            self.refresh_devices()
            self.new_device_name.delete(0, tk.END)
        else:
            messagebox.showerror("Error", f"Failed to add device: {response.json().get('error', 'Unknown error')}")

    def search_devices(self):
        query = self.search_query.get().lower()
        response = requests.get(f"{API_URL}/devices")
        if response.status_code == 200:
            devices = response.json()
            self.device_tree.delete(*self.device_tree.get_children())  # Clear existing data
            for device_id, device_info in devices.items():
                if query in device_id.lower():
                    last_checked = datetime.strptime(device_info['last_checked'], "%a, %d %b %Y %H:%M:%S %Z")
                    self.device_tree.insert("", "end", values=(
                        device_id,
                        device_info['status'],
                        last_checked
                    ))
        else:
            messagebox.showerror("Error", "Failed to retrieve device data")

    def delete_device(self):
        selected_item = self.device_tree.selection()
        if not selected_item:
            messagebox.showwarning("Selection Error", "Please select a device to delete.")
            return

        device_name = self.device_tree.item(selected_item)['values'][0]
        response = requests.delete(f"{API_URL}/device/{device_name}")
        if response.status_code == 200:
            messagebox.showinfo("Success", "Device deleted successfully!")
            self.refresh_devices()
        else:
            messagebox.showerror("Error", "Failed to delete device.")

    def parse_date(self, date_string):
        return datetime.strptime(date_string, "%a, %d %b %Y %H:%M:%S %Z")

    def change_device_status_func(self):
        selected_item = self.device_tree.selection()
        if not selected_item:
            messagebox.showwarning("Selection Error", "Please select a device to change its status.")
            return

        device_name = self.device_tree.item(selected_item)['values'][0]
        new_status = self.change_device_status.get()

        response = requests.post(f"{API_URL}/device/{device_name}/event", json={'event_type': new_status})
        if response.status_code == 201:
            data = response.json()
            # Parse and format the date consistently
            last_checked = self.parse_date(data['last_checked'])
            self.device_tree.item(selected_item, values=(
                device_name,
                data['status'],
                last_checked.strftime("%Y-%m-%d %H:%M:%S")
            ))
            messagebox.showinfo("Success", "Device status updated successfully!")
        else:
            messagebox.showerror("Error", f"Failed to update device status: {response.json().get('error', 'Unknown error')}")



if __name__ == "__main__":
    root = tk.Tk()
    app = DeviceMonitoringApp(root)
    root.mainloop()
