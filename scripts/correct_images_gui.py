import os
import subprocess
import tkinter as tk
from tkinter import filedialog, messagebox

SCRIPT_PATH = os.path.join(os.path.dirname(__file__), "correct_images.py")


class CorrectImagesApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Sentera Radiometric Corrections")
        self.geometry("650x500")
        self.create_widgets()

    def create_widgets(self):
        row = 0
        tk.Label(self, text="Input Path (folder)").grid(
            row=row, column=0, sticky="w", padx=5
        )
        self.input_path_var = tk.StringVar()
        tk.Entry(
            self, textvariable=self.input_path_var, width=50, justify="right"
        ).grid(row=row, column=1, sticky="e", padx=(0, 5))
        tk.Button(self, text="Browse", command=self.browse_input).grid(
            row=row, column=2
        )
        row += 1

        tk.Label(self, text="Output Path (folder)").grid(
            row=row, column=0, sticky="w", padx=5
        )
        self.output_path_var = tk.StringVar()
        tk.Entry(
            self, textvariable=self.output_path_var, width=50, justify="right"
        ).grid(row=row, column=1, sticky="e", padx=(0, 5))
        tk.Button(self, text="Browse", command=self.browse_output).grid(
            row=row, column=2
        )
        row += 1

        tk.Label(self, text="Calibration ID").grid(
            row=row, column=0, sticky="w", padx=5
        )
        self.calibration_id_var = tk.StringVar(value="CAL")
        tk.Entry(self, textvariable=self.calibration_id_var).grid(
            row=row, column=1, padx=(0, 5)
        )
        row += 1

        self.no_ils_var = tk.BooleanVar(value=True)
        tk.Checkbutton(self, text="No ILS Correction", variable=self.no_ils_var).grid(
            row=row, column=0, sticky="w", padx=5
        )
        row += 1

        self.no_reflectance_var = tk.BooleanVar()
        tk.Checkbutton(
            self, text="No Reflectance Correction", variable=self.no_reflectance_var
        ).grid(row=row, column=0, sticky="w", padx=5)
        row += 1

        self.all_panels_var = tk.BooleanVar()
        tk.Checkbutton(
            self,
            text="Use All Panels for Reflectance Correction",
            variable=self.all_panels_var,
        ).grid(row=row, column=0, sticky="w", padx=5)
        row += 1

        self.delete_original_var = tk.BooleanVar()
        tk.Checkbutton(
            self,
            text="Delete/Overwrite Original Images",
            variable=self.delete_original_var,
        ).grid(row=row, column=0, sticky="w", padx=5)
        row += 1

        tk.Label(self, text="ExifTool Path (optional)").grid(
            row=row, column=0, sticky="w", padx=5
        )
        self.exiftool_path_var = tk.StringVar()
        tk.Entry(self, textvariable=self.exiftool_path_var, width=40).grid(
            row=row, column=1, padx=(0, 5)
        )
        tk.Button(self, text="Browse", command=self.browse_exiftool).grid(
            row=row, column=2
        )
        row += 1

        self.uint16_var = tk.BooleanVar()
        tk.Checkbutton(
            self, text="Output as uint16 (0-65535)", variable=self.uint16_var
        ).grid(row=row, column=0, sticky="w", padx=5)
        row += 1

        # Output text box
        self.output_text = tk.Text(self, height=10, width=70)
        self.output_text.grid(row=row, column=0, columnspan=3)
        row += 1

        # Run Correction button at the bottom
        self.run_button = tk.Button(
            self,
            text="Run Correction",
            command=self.run_correction,
            bg="green",
            fg="white",
        )
        self.run_button.grid(row=row, column=0, columnspan=3, pady=20)
        row += 1

    def browse_input(self):
        path = filedialog.askdirectory()
        if path:
            self.input_path_var.set(path)
            # Set output path to input path + '-calibrated'
            calibrated_path = path.rstrip("/\\") + "-calibrated"
            self.output_path_var.set(calibrated_path)
            # Scroll input Entry to the end
            entry_widget = self.nametowidget(self.children["!entry"])
            entry_widget.icursor(tk.END)
            entry_widget.xview_moveto(1)
            # Scroll output Entry to the end
            output_entry_widget = self.nametowidget(self.children["!entry2"])
            output_entry_widget.icursor(tk.END)
            output_entry_widget.xview_moveto(1)

    def browse_output(self):
        path = filedialog.askdirectory()
        if path:
            self.output_path_var.set(path)
            # Scroll output Entry to the end
            entry_widget = self.nametowidget(self.children["!entry2"])
            entry_widget.icursor(tk.END)
            entry_widget.xview_moveto(1)

    def browse_exiftool(self):
        path = filedialog.askopenfilename(filetypes=[("Executable", "*.exe")])
        if path:
            self.exiftool_path_var.set(path)

    def run_correction(self):
        import threading

        input_path = self.input_path_var.get()
        if not input_path:
            messagebox.showerror("Error", "Input path is required.")
            return
        cmd = ["python", "-u", SCRIPT_PATH, input_path]
        if self.calibration_id_var.get():
            cmd += ["--calibration_id", self.calibration_id_var.get()]
        if self.output_path_var.get():
            cmd += ["--output_path", self.output_path_var.get()]
        if self.no_ils_var.get():
            cmd.append("--no_ils_correct")
        if self.no_reflectance_var.get():
            cmd.append("--no_reflectance_correct")
        if self.all_panels_var.get():
            cmd.append("--all_panels")
        if self.delete_original_var.get():
            cmd.append("--delete_original")
        if self.exiftool_path_var.get():
            cmd += ["--exiftool_path", self.exiftool_path_var.get()]
        if self.uint16_var.get():
            cmd.append("--uint16_output")
        self.output_text.delete(1.0, tk.END)
        self.output_text.insert(tk.END, f"Running: {' '.join(cmd)}\n")

        def run_subprocess():
            try:
                process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    bufsize=1,
                )

                def read_stdout(stream):
                    for line in iter(stream.readline, ""):
                        if line:
                            self.output_text.after(
                                0, self.output_text.insert, tk.END, line
                            )
                    stream.close()

                def read_stderr(stream):
                    for line in iter(stream.readline, ""):
                        if line:
                            # Replace all text with error output
                            self.output_text.after(
                                0, self.output_text.delete, 1.0, tk.END
                            )
                            self.output_text.after(
                                0, self.output_text.insert, tk.END, line
                            )
                    stream.close()

                stdout_thread = threading.Thread(
                    target=read_stdout, args=(process.stdout,)
                )
                stderr_thread = threading.Thread(
                    target=read_stderr, args=(process.stderr,)
                )
                stdout_thread.start()
                stderr_thread.start()
                stdout_thread.join()
                stderr_thread.join()
            except Exception as e:
                self.output_text.after(0, self.display_exception, e)

        threading.Thread(target=run_subprocess, daemon=True).start()

    def display_output(self, stdout, stderr):
        if stdout:
            self.output_text.insert(tk.END, stdout)
        if stderr:
            self.output_text.insert(tk.END, "\nErrors:\n" + stderr)

    def display_exception(self, e):
        self.output_text.insert(tk.END, f"\nException: {e}")


if __name__ == "__main__":
    app = CorrectImagesApp()
    app.mainloop()
