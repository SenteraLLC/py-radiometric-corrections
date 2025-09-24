import os
import subprocess
import sys
import tkinter as tk
from tkinter import filedialog, messagebox

SCRIPT_PATH = os.path.join(os.path.dirname(__file__), "correct_images.py")


class CorrectImagesApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Sentera Radiometric Corrections")
        self.geometry("600x500")
        self.iconbitmap("sentera_radiometric_corrections_icon.ico")
        self.create_widgets()

    def create_widgets(self):
        row = 0
        tk.Label(self, text="Input Path").grid(row=row, column=0, sticky="w", padx=15)
        self.input_path_var = tk.StringVar()
        tk.Entry(
            self, textvariable=self.input_path_var, width=50, justify="right"
        ).grid(row=row, column=1, sticky="e", padx=(0, 5))
        self.browse_input_button = tk.Button(
            self, text="Browse", command=self.browse_input
        )
        self.browse_input_button.grid(row=row, column=2)
        row += 1

        tk.Label(self, text="Output Path").grid(row=row, column=0, sticky="w", padx=15)
        self.output_path_var = tk.StringVar()
        tk.Entry(
            self, textvariable=self.output_path_var, width=50, justify="right"
        ).grid(row=row, column=1, sticky="e", padx=(0, 5))
        self.browse_output_button = tk.Button(
            self, text="Browse", command=self.browse_output
        )
        self.browse_output_button.grid(row=row, column=2)
        row += 1

        self.reflectance_var = tk.BooleanVar(value=True)
        tk.Checkbutton(
            self, text="Reflectance Correction", variable=self.reflectance_var
        ).grid(row=row, column=0, sticky="w", padx=15)

        self.ils_var = tk.BooleanVar(value=False)
        tk.Checkbutton(self, text="ILS Correction", variable=self.ils_var).grid(
            row=row, column=1, sticky="w", padx=15
        )
        row += 1

        self.advanced_options = tk.BooleanVar()
        tk.Checkbutton(
            self,
            text="Advanced Options",
            variable=self.advanced_options,
            command=self.toggle_advanced_options,
        ).grid(row=row, column=0, sticky="w", padx=15)

        row += 1

        self.exiftool_path_var = tk.StringVar()
        self.exiftool_path_label = tk.Label(self, text="ExifTool Path (optional)")
        self.exiftool_path_label.grid(row=row, column=0, sticky="w", padx=15)
        self.exiftool_entry = tk.Entry(
            self, textvariable=self.exiftool_path_var, width=50, justify="right"
        )
        self.exiftool_entry.grid(row=row, column=1, sticky="w", padx=(0, 5))
        self.exiftool_path_browse_button = tk.Button(
            self, text="Browse", command=self.browse_exiftool
        )
        self.exiftool_path_browse_button.grid(row=row, column=2)
        row += 1

        self.calibration_id_var = tk.StringVar(value="CAL")
        self.cal_id_label = tk.Label(self, text="Calibration ID")
        self.cal_id_label.grid(row=row, column=0, sticky="w", padx=15)
        self.cal_id_entry = tk.Entry(self, textvariable=self.calibration_id_var)
        self.cal_id_entry.grid(row=row, column=1, sticky="w")
        row += 1

        self.all_panels_var = tk.BooleanVar()
        self.all_panels_checkbutton = tk.Checkbutton(
            self,
            text="Use All Panel sets(6X)",
            variable=self.all_panels_var,
        )
        self.all_panels_checkbutton.grid(row=row, column=0, sticky="w", padx=15)
        row += 1

        self.delete_original_var = tk.BooleanVar()
        self.delete_overwrite_checkbutton = tk.Checkbutton(
            self,
            text="Delete/Overwrite Original Images",
            variable=self.delete_original_var,
        )
        self.delete_overwrite_checkbutton.grid(row=row, column=0, sticky="w", padx=15)
        row += 1

        self.uint16_var = tk.BooleanVar()
        self.uint16_checkbutton = tk.Checkbutton(
            self, text="Output as uint16 (0-65535)", variable=self.uint16_var
        )
        self.uint16_checkbutton.grid(row=row, column=0, sticky="w", padx=15)

        self.toggle_advanced_options()

        row += 1

        # Run Correction button at the bottom
        self.run_button = tk.Button(
            self,
            text="Run Correction",
            command=self.run_correction,
            bg="green",
            fg="white",
            width=70,
        )
        self.run_button.grid(row=row, column=0, columnspan=3, pady=20)
        row += 1

        # Output text box
        self.output_text = tk.Text(self, height=10, width=70)
        self.output_text.grid(
            row=row, column=0, sticky="ew", columnspan=3, padx=(15, 15)
        )

    def toggle_advanced_options(self):
        widgets = [
            self.cal_id_label,
            self.cal_id_entry,
            self.all_panels_checkbutton,
            self.delete_overwrite_checkbutton,
            self.exiftool_path_label,
            self.exiftool_entry,
            self.exiftool_path_browse_button,
            self.uint16_checkbutton,
        ]
        if not self.advanced_options.get():
            for widget in widgets:
                widget.grid_remove()
        else:
            for widget in widgets:
                widget.grid()

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

    def disable_buttons(self):
        self.run_button["state"] = "disabled"
        self.browse_input_button["state"] = "disabled"
        self.browse_output_button["state"] = "disabled"
        self.exiftool_path_browse_button["state"] = "disabled"

    def enable_buttons(self):
        self.run_button["state"] = "normal"
        self.browse_input_button["state"] = "normal"
        self.browse_output_button["state"] = "normal"
        self.exiftool_path_browse_button["state"] = "normal"

    def run_correction(self):
        import threading

        self.disable_buttons()
        input_path = self.input_path_var.get()
        if not input_path:
            messagebox.showerror("Error", "Input path is required.")
            return
        cmd = ["python", "-u", SCRIPT_PATH, input_path]
        if self.calibration_id_var.get():
            cmd += ["--calibration_id", self.calibration_id_var.get()]
        if self.output_path_var.get():
            cmd += ["--output_path", self.output_path_var.get()]
        if not self.ils_var.get():
            cmd.append("--no_ils_correct")
        if not self.reflectance_var.get():
            cmd.append("--no_reflectance_correct")
        if self.all_panels_var.get():
            cmd.append("--all_panels")
        if self.delete_original_var.get():
            cmd.append("--delete_original")
        if self.exiftool_path_var.get():
            cmd += ["--exiftool_path", self.exiftool_path_var.get()]
        else:
            cmd += ["--exiftool_path", os.path.join(sys._MEIPASS, "exiftool.exe")]
        if self.uint16_var.get():
            cmd.append("--uint16_output")
        self.output_text.delete(1.0, tk.END)
        self.output_text.insert(tk.END, f"Running: {' '.join(cmd)}\n")

        os.makedirs(self.output_path_var.get(), exist_ok=True)

        def run_subprocess():
            try:
                # Open the output file for writing
                with open(
                    os.path.join(
                        os.path.split(self.output_path_var.get())[0],
                        f"{os.path.split(self.output_path_var.get())[1]}_corrections_log.txt",
                    ),
                    "w",
                    encoding="utf-8",
                ) as outfile:
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
                                outfile.write(line)
                                outfile.flush()
                        stream.close()

                    def read_stderr(stream):
                        for line in iter(stream.readline, ""):
                            if line:
                                self.output_text.after(
                                    0, self.output_text.delete, 1.0, tk.END
                                )
                                self.output_text.after(
                                    0, self.output_text.insert, tk.END, line
                                )
                                outfile.write(line)
                                outfile.flush()
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
            self.enable_buttons()

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
