import logging
import os
import sys
import threading
import tkinter as tk
from tkinter import filedialog, messagebox

from imgcorrect import corrections

logger = logging.getLogger(__name__)


class TextHandler(logging.Handler):
    def __init__(self, text_widget):
        super().__init__()
        self.text_widget = text_widget

    def emit(self, record):
        msg = self.format(record)
        # Get the index of the last line
        last_line_index = self.text_widget.index("end-2l")
        last_line_text = self.text_widget.get(last_line_index, "end-1c").strip()
        if last_line_text and last_line_text[0].isdigit():
            # Replace the last line
            self.text_widget.after(
                0, self.text_widget.delete, last_line_index, "end-1c"
            )
            self.text_widget.after(0, self.text_widget.insert, tk.END, msg + "\n")
        else:
            self.text_widget.after(0, self.text_widget.insert, tk.END, msg + "\n")
        self.text_widget.after(0, self.text_widget.see, tk.END)


class CorrectImagesApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Sentera Radiometric Corrections")
        self.geometry("600x500")
        self.resizable(True, False)  # Allow horizontal resize, disable vertical resize
        self.minsize(600, 500)  # Set minimum width to 600px, height to 500px
        try:
            self.iconbitmap(
                os.path.join(sys._MEIPASS, "sentera_radiometric_corrections_icon.ico")
            )
        except Exception:
            self.iconbitmap("sentera_radiometric_corrections_icon.ico")
        self.create_widgets()
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(10, weight=1)  # Make the output text box row expandable

    def create_widgets(self):
        row = 0
        tk.Label(self, text="Input Path").grid(
            row=row, column=0, sticky="w", padx=(15, 0)
        )
        self.input_path_var = tk.StringVar()
        tk.Entry(self, textvariable=self.input_path_var, width=90).grid(
            row=row, column=1, sticky="ew"
        )
        self.browse_input_button = tk.Button(
            self, text="Browse", command=self.browse_input
        )
        self.browse_input_button.grid(row=row, column=2, sticky="ew", padx=(0, 5))
        row += 1

        tk.Label(self, text="Output Path").grid(
            row=row, column=0, sticky="w", padx=(15, 0)
        )
        self.output_path_var = tk.StringVar()
        self.output_path_text = tk.Entry(
            self, textvariable=self.output_path_var, width=90
        )
        self.output_path_text.grid(row=row, column=1, sticky="ew")
        self.browse_output_button = tk.Button(
            self, text="Browse", command=self.browse_output
        )
        self.browse_output_button.grid(row=row, column=2, sticky="w", padx=(0, 5))
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
        self.exiftool_path_label.grid(row=row, column=0, sticky="w", padx=(15, 0))
        self.exiftool_entry = tk.Entry(
            self, textvariable=self.exiftool_path_var, width=90
        )
        self.exiftool_entry.grid(row=row, column=1, sticky="ew")
        self.exiftool_path_browse_button = tk.Button(
            self, text="Browse", command=self.browse_exiftool
        )
        self.exiftool_path_browse_button.grid(row=row, column=2, padx=(0, 5))
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
            text="Use All Panel Sets (6X)",
            variable=self.all_panels_var,
        )
        self.all_panels_checkbutton.grid(row=row, column=0, sticky="w", padx=15)
        row += 1

        self.delete_original_var = tk.BooleanVar()
        self.delete_overwrite_checkbutton = tk.Checkbutton(
            self,
            text="Delete/Overwrite Original",
            variable=self.delete_original_var,
            command=self.toggle_overwrite,
        )
        self.delete_overwrite_checkbutton.grid(row=row, column=0, sticky="w", padx=15)
        row += 1

        self.uint16_var = tk.BooleanVar()
        self.uint16_checkbutton = tk.Checkbutton(
            self, text="Output as UInt16 (0-65535)", variable=self.uint16_var
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
            row=row, column=0, sticky="nsew", columnspan=3, padx=(15, 15), pady=(0, 15)
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

    def toggle_overwrite(self):
        if self.delete_original_var.get():
            self.output_path_var.set(self.input_path_var.get())
            self.browse_output_button["state"] = "disabled"
            self.output_path_text["state"] = "disabled"
        else:
            self.browse_output_button["state"] = "normal"
            self.output_path_text["state"] = "normal"

    def browse_input(self):
        path = filedialog.askdirectory()
        if path:
            self.input_path_var.set(path)
            # Set output path to input path + '-calibrated'
            if not self.delete_original_var.get():
                calibrated_path = path.rstrip("/\\") + "-calibrated"
            else:
                calibrated_path = path
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

        self.disable_buttons()
        input_path = self.input_path_var.get()
        if not input_path:
            messagebox.showerror("Error", "Input path is required.")
            self.enable_buttons()
            return
        calibration_id = self.calibration_id_var.get()
        output_path = self.output_path_var.get()
        no_ils_correct = not self.ils_var.get()
        no_reflectance_correct = not self.reflectance_var.get()
        all_panels = self.all_panels_var.get()
        delete_original = self.delete_original_var.get()

        if self.exiftool_path_var.get():
            exiftool_path = self.exiftool_path_var.get()
        else:
            exiftool_path = os.path.join(sys._MEIPASS, "exiftool.exe")
        uint16_output = self.uint16_var.get()

        self.output_text.delete(1.0, tk.END)

        os.makedirs(self.output_path_var.get(), exist_ok=True)

        def run_corrections():
            handler = TextHandler(self.output_text)
            logging.basicConfig(
                filename=os.path.join(
                    os.path.split(output_path)[0],
                    f"{os.path.basename(output_path)}_radiometric_corrections.log",
                ),
                level=logging.INFO,
                format="%(asctime)s %(levelname)s:%(message)s",
            )
            logging.getLogger().addHandler(handler)
            logger.info("Running Corrections")
            logger.info(f"Input Path: {input_path}")
            logger.info(f"Output Path: {output_path}")
            logger.info(f"ExifTool Path: {exiftool_path}")
            logger.info(f"Reflectance Correction: {not no_reflectance_correct}")
            logger.info(f"ILS Correction: {not no_ils_correct}")
            logger.info(f"Calibration ID: {calibration_id}")
            logger.info(f"All Panels: {all_panels}")
            logger.info(f"Delete Original: {delete_original}")
            logger.info(f"UInt16 Output: {uint16_output}")
            corrections.correct_images(
                input_path,
                calibration_id,
                output_path,
                no_ils_correct,
                no_reflectance_correct,
                all_panels,
                delete_original,
                exiftool_path,
                uint16_output,
            )
            self.enable_buttons()
            logger.info("Corrections complete!")

        threading.Thread(target=run_corrections, daemon=True).start()

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
