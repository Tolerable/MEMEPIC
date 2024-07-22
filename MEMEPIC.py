import os
import io
import cv2
import json
import numpy as np
import tkinter as tk
from tkinter import filedialog, colorchooser, IntVar, StringVar, Checkbutton, Entry, Label, Button, Scale, Toplevel, Canvas, Menu, messagebox
from PIL import Image, ImageTk, ImageGrab
import win32clipboard as clp
from datetime import datetime

CONFIG_FILE = "config.json"
EXAMPLE_IMAGE = '.\\IMAGES\\EXAMPLE.png'

def mask_path(path):
    user_home = os.path.expanduser("~")
    if path.startswith(user_home):
        drive, tail = os.path.splitdrive(user_home)
        masked_path = os.path.join(drive, "Users", "****", tail[1:], path[len(user_home):])
        return masked_path
    else:
        return path

def unmask_path(path):
    if "****" in path:
        path_parts = path.split("****")
        user_home = os.path.expanduser("~")
        return os.path.join(user_home, *path_parts[1:])
    else:
        return path

def create_polaroid(image, border_size=50):
    width, height = image.size
    new_width = width + 2 * border_size
    new_height = height + 4 * border_size  # Increased bottom border
    polaroid = Image.new('RGBA', (new_width, new_height), (255, 255, 255, 255))
    polaroid.paste(image, (border_size, border_size))
    return polaroid

def normalize_path(path):
    return os.path.normpath(path).replace('\\', '/')

class MEMEPICApp:
    def __init__(self, root):
        self.root = root
        self.root.title("MEM PIC")
        self.root.geometry("620x725")

        # Set default output folder
        default_output_folder = os.path.join(os.path.expanduser("~"), "Pictures", "MemePic")
        if not os.path.exists(default_output_folder):
            os.makedirs(default_output_folder)

        self.create_widgets()

        # Set a fixed size for the image label
        self.img_label.config(width=300, height=300)
        self.img_label.grid_propagate(False)

        self.set_image_window_size()

        self.load_sample_image()

        self.root.protocol("WM_DELETE_WINDOW", lambda: (self.save_settings(), self.root.destroy()))
        self.load_settings()

        # Set default output folder if not set in settings
        if not self.entry_output_folder.get():
            self.entry_output_folder.insert(0, default_output_folder)

    def set_image_window_size(self):
        # Limit the window size when no image is loaded
        self.root.update_idletasks()  # Update the window size based on widgets
        self.root.geometry(f"{self.root.winfo_width()}x{self.root.winfo_height()}")  # Set the window size

    def load_sample_image(self):
        sample_image_path = EXAMPLE_IMAGE
        if os.path.exists(sample_image_path):
            self.image = Image.open(sample_image_path).convert("RGBA")
            self.update_image_label()
        else:
            self.img_label.config(text="Sample Image Not Found")

    def update_image_label(self):
        if self.image:
            # Resize the image to fit within the label while maintaining aspect ratio
            img_resized = self.resize_image(self.image, 300, 300)
            img_display = ImageTk.PhotoImage(img_resized)
            self.img_label.config(image=img_display, text="")
            self.img_label.image = img_display
        else:
            self.img_label.config(text="No Image Loaded")

    def resize_image(self, image, max_width, max_height):
        width_ratio = max_width / image.width
        height_ratio = max_height / image.height
        new_ratio = min(width_ratio, height_ratio)
        new_width = int(image.width * new_ratio)
        new_height = int(image.height * new_ratio)
        return image.resize((new_width, new_height), Image.LANCZOS)

    def make_transparent(self, image):
        if self.var_transparency.get() != 1:
            return image  # Return the original image if transparency is not set
        
        data = np.array(image)
        if data.shape[2] == 3:  # RGB image
            rgb = data
            alpha = np.full((data.shape[0], data.shape[1]), 255, dtype=np.uint8)
        else:  # RGBA image
            rgb = data[:,:,:3]
            alpha = data[:,:,3]

        # Make only pure white (255, 255, 255) transparent
        mask = (rgb == [255, 255, 255]).all(axis=2)
        alpha[mask] = 0

        return Image.fromarray(np.dstack((rgb, alpha)))

    def copy_to_clipboard_method(self):
        self.update_image_with_settings()
        if hasattr(self, 'processed_image') and self.processed_image is not None:
            try:
                temp_file = './temp_image.png'
                image_to_copy = self.processed_image.copy()
                
                if self.var_transparency.get() == 1:
                    # If transparency is selected, keep the image as is (with transparency)
                    if image_to_copy.mode != 'RGBA':
                        image_to_copy = image_to_copy.convert('RGBA')
                else:
                    # If transparency is not selected, ensure opaque background
                    if image_to_copy.mode in ('RGBA', 'LA'):
                        background = Image.new(image_to_copy.mode[:-1], image_to_copy.size, (255, 255, 255))
                        background.paste(image_to_copy, mask=image_to_copy.split()[-1])
                        image_to_copy = background.convert('RGB')
                
                image_to_copy.save(temp_file, format="PNG")

                clp.OpenClipboard()
                clp.EmptyClipboard()

                wide_path = os.path.abspath(temp_file).encode('utf-16-le') + b'\0'
                clp.SetClipboardData(clp.RegisterClipboardFormat('FileNameW'), wide_path)

                with open(temp_file, 'rb') as f:
                    clp.SetClipboardData(clp.RegisterClipboardFormat('PNG'), f.read())

                clp.CloseClipboard()

                print(f"Image copied to clipboard and saved as {temp_file}")
            except Exception as e:
                print(f"Error copying image to clipboard: {e}")
        else:
            print("No processed image available to copy")
        
    def update_image_with_settings(self):
        if self.image is None:
            print("No image loaded.")
            return

        working_image = self.image.copy()

        slogan = self.entry_slogan.get("1.0", "end-1c")
        font_size = self.scale_font_size.get()
        font_thickness = self.scale_font_thickness.get()
        font_color = self.color_var.get() or '255,255,255'
        outline_color = self.outline_color_var.get() or '0,0,0'
        outline_thickness = self.scale_outline_thickness.get() + 2 if self.scale_outline_thickness.get() > 0 else 0
        box_color = self.box_color_var.get() or '0,0,0'
        box_opacity = self.scale_box_opacity.get() / 100.0
        use_box = box_opacity > 0
        text_position = self.scale_text_position.get()
        box_width = self.scale_box_width.get()

        working_image = self.add_slogan_to_image(working_image, slogan, font_color, font_thickness, font_size, outline_color, outline_thickness, box_color, box_opacity, use_box, text_position, box_width)

        if working_image:
            self.processed_image = working_image
            display_image = working_image.copy()
            
            if self.var_transparency.get() == 1:
                display_image = self.make_transparent(display_image)
            
            display_image = self.resize_image(display_image, 300, 300)
            self.updated_image = ImageTk.PhotoImage(display_image)
            self.img_label.config(image=self.updated_image)
            self.img_label.image = self.updated_image
        else:
            print("Failed to update image with settings")

    def add_slogan_to_image(self, image, slogan_text, font_color_str, font_thickness, font_scale, outline_color_str, outline_thickness, box_color_str, box_opacity, use_box, text_position, box_width):
        if image is None:
            print("No image loaded.")
            return None

        image_np = np.array(image)
        if image_np.shape[2] == 3:
            image_np = cv2.cvtColor(image_np, cv2.COLOR_RGB2RGBA)
        elif image_np.shape[2] == 4:
            pass
        else:
            print("Unsupported image format")
            return None

        font = cv2.FONT_HERSHEY_SIMPLEX
        image_height, image_width = image_np.shape[:2]

        lines = slogan_text.split('\n')
        if all(line == '' for line in lines):
            return Image.fromarray(image_np)

        max_line_height = cv2.getTextSize('Tg', font, font_scale, int(font_thickness))[0][1]
        
        text_sizes = [cv2.getTextSize(line, font, font_scale, int(font_thickness))[0] for line in lines]
        text_width = max(size[0] for size in text_sizes)
        text_height = max_line_height * len(lines)
        line_spacing = int(max_line_height * 0.3)
        line_padding = 9  # Add padding between lines
        total_height = text_height + (len(lines) - 1) * (line_spacing + line_padding)
        
        while text_width > image_width and font_scale > 0.5:
            font_scale -= 0.1
            max_line_height = cv2.getTextSize('Tg', font, font_scale, int(font_thickness))[0][1]
            text_sizes = [cv2.getTextSize(line, font, font_scale, int(font_thickness))[0] for line in lines]
            text_width = max(size[0] for size in text_sizes)
            text_height = max_line_height * len(lines)
            line_spacing = int(max_line_height * 0.3)
            total_height = text_height + (len(lines) - 1) * (line_spacing + line_padding)

        text_position = text_position / 100.0
        text_y = int(text_position * (image_height - total_height)) + max_line_height

        text_x = (image_width - text_width) // 2

        padding = int(max_line_height * 0.2)

        font_color = tuple(int(c) for c in font_color_str.split(',')[:3])
        box_color = tuple(int(c) for c in box_color_str.split(',')[:3])
        outline_color = tuple(int(c) for c in outline_color_str.split(',')[:3]) if outline_color_str and outline_thickness > 0 else None

        if use_box:
            box_width_pixels = int(image_width * (box_width / 100))
            rect_left = max(0, (image_width - box_width_pixels) // 2)
            rect_right = min(image_width, rect_left + box_width_pixels)
            rect_top = max(0, text_y - max_line_height - padding - line_padding)
            rect_bottom = min(image_height, text_y + total_height - max_line_height + padding + line_padding)
            overlay = image_np.copy()
            cv2.rectangle(overlay, (rect_left, rect_top), (rect_right, rect_bottom), box_color + (255,), -1)
            cv2.addWeighted(overlay, box_opacity, image_np, 1 - box_opacity, 0, image_np)

        for i, line in enumerate(lines):
            line_y = text_y + i * (max_line_height + line_spacing + line_padding)
            if 0 <= line_y <= image_height:
                line_x = text_x  # Left-align the text within the box
                
                if outline_thickness > 0 and outline_color is not None:
                    for dx in range(-outline_thickness, outline_thickness + 1):
                        for dy in range(-outline_thickness, outline_thickness + 1):
                            if dx != 0 or dy != 0:
                                cv2.putText(image_np, line, (line_x + dx, line_y + dy), font, font_scale, outline_color + (255,), outline_thickness)
                cv2.putText(image_np, line, (line_x, line_y), font, font_scale, font_color + (255,), font_thickness)

        return Image.fromarray(image_np)
    
    def reload_image(self):
        self.load_image(self.entry_image_path.get())

    def show_image(self, image_path):
        top = Toplevel()
        top.title("Processed Image")
        img = Image.open(image_path)
        img = img.resize((800, 800), Image.LANCZOS)
        img = ImageTk.PhotoImage(img)
        img_label = Label(top, image=img)
        img_label.image = img
        img_label.pack()
        Button(top, text="Close", command=top.destroy).pack()

    def load_config(self):
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, 'r') as file:
                return json.load(file)
        return {}

    def save_config(self, config):
        with open(CONFIG_FILE, 'w') as file:
            json.dump(config, file)

    def on_save(self):
        if hasattr(self, 'processed_image') and self.processed_image is not None:
            output_folder = self.entry_output_folder.get()
            if not os.path.exists(output_folder):
                os.makedirs(output_folder)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            file_name = f"meme_{timestamp}.png"
            file_path = os.path.normpath(os.path.join(output_folder, file_name))
            
            saved_image = self.processed_image.copy()
            # Only apply transparency if it's explicitly set
            if self.var_transparency.get() == 1:
                saved_image = self.make_transparent(saved_image)
            
            saved_image.save(file_path, "PNG")
            print(f"Image saved to {file_path}")
        else:
            print("No processed image available to save")

    def create_widgets(self):
        toolbar = tk.Menu(self.root)
        self.root.config(menu=toolbar)

        view_menu = tk.Menu(toolbar, tearoff=0)
        toolbar.add_cascade(label="Options", menu=view_menu)
        self.on_top = IntVar()
        view_menu.add_checkbutton(label="On Top", variable=self.on_top, command=lambda: self.root.attributes('-topmost', self.on_top.get()))

        help_menu = tk.Menu(toolbar, tearoff=0)
        toolbar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="About", command=self.show_about)

        content_frame = tk.Frame(self.root)
        content_frame.grid(row=0, column=0, padx=10, pady=10)

        Label(content_frame).grid(row=0, column=0, padx=5, pady=5, sticky='we')
        self.entry_output_folder = Entry(content_frame, width=40)
        self.entry_output_folder.grid(row=0, column=1, columnspan=2, padx=5, pady=5, sticky='we')
        Button(content_frame, text="OUTPUT FOLDER", command=self.set_output_folder).grid(row=0, column=0, padx=5, pady=5, sticky='we')

        Label(content_frame).grid(row=1, column=0, padx=5, pady=5, sticky='we')
        Button(content_frame, text="IMAGE", command=self.select_image).grid(row=1, column=0, padx=5, pady=5, sticky='we')
        self.entry_image_path = Entry(content_frame, width=50)
        self.entry_image_path.grid(row=1, column=1, columnspan=2, padx=5, pady=5, sticky='w')
        self.entry_image_path.insert(0, EXAMPLE_IMAGE)

        self.img_label = Label(content_frame, width=300, height=300, bd=1, relief='solid', anchor='center', text="No Image Loaded")
        self.img_label.grid(row=2, column=0, columnspan=3, padx=5, pady=5)

        self.scale_text_position = Scale(content_frame, from_=0, to=100, orient=tk.VERTICAL, length=300, command=lambda value: self.update_sample_text())
        self.scale_text_position.grid(row=2, column=3, padx=5, pady=5, sticky='ns')

        font_frame = tk.Frame(content_frame)
        font_frame.grid(row=3, column=0, columnspan=4, pady=5)

        self.scale_font_size = Scale(font_frame, from_=1, to=5, orient=tk.HORIZONTAL, length=150, command=lambda value: self.update_sample_text())
        self.scale_font_size.grid(row=0, column=0, padx=5, pady=5, sticky='w')
        Label(font_frame, text="SIZE").grid(row=0, column=0, padx=5, pady=5, sticky='n')

        self.scale_font_thickness = Scale(font_frame, from_=1, to=10, orient=tk.HORIZONTAL, length=150, command=lambda value: self.update_sample_text())
        self.scale_font_thickness.grid(row=0, column=1, padx=5, pady=5, sticky='w')
        Label(font_frame, text="THICK").grid(row=0, column=1, padx=5, pady=5, sticky='n')

        self.scale_outline_thickness = Scale(font_frame, from_=0, to=5, orient=tk.HORIZONTAL, length=150, command=lambda value: self.update_sample_text())
        self.scale_outline_thickness.grid(row=0, column=2, padx=5, pady=5, sticky='w')
        Label(font_frame, text="OUTLINE").grid(row=0, column=2, padx=5, pady=5, sticky='n')

        color_frame = tk.Frame(content_frame)
        color_frame.grid(row=4, column=0, columnspan=4, pady=10)

        Button(color_frame, text="Polaroid", command=self.apply_polaroid).grid(row=0, column=0, padx=5, pady=5, sticky='w')
        Button(color_frame, text="Font Color", command=lambda: self.update_color_label(self.color_var, self.color_canvas)).grid(row=0, column=1, padx=5, pady=5, sticky='w')
        self.color_var = StringVar()
        self.color_canvas = Canvas(color_frame, width=20, height=20, bg='white', bd=1, relief='solid')
        self.color_canvas.grid(row=0, column=2, padx=5, pady=5, sticky='w')
        self.color_canvas.bind("<Button-1>", lambda event: self.update_color_label(self.color_var, self.color_canvas))

        Button(color_frame, text="Outline Color", command=lambda: self.update_color_label(self.outline_color_var, self.outline_canvas)).grid(row=0, column=3, padx=5, pady=5, sticky='w')
        self.outline_color_var = StringVar()
        self.outline_canvas = Canvas(color_frame, width=20, height=20, bg='white', bd=1, relief='solid')
        self.outline_canvas.grid(row=0, column=4, padx=5, pady=5, sticky='w')
        self.outline_canvas.bind("<Button-1>", lambda event: self.update_color_label(self.outline_color_var, self.outline_canvas))

        box_frame = tk.Frame(content_frame)
        box_frame.grid(row=5, column=0, columnspan=4, pady=10)

        Button(box_frame, text="Box Color", command=lambda: self.update_color_label(self.box_color_var, self.box_canvas)).grid(row=0, column=0, padx=5, pady=5, sticky='w')
        self.box_color_var = StringVar()
        self.box_canvas = Canvas(box_frame, width=20, height=20, bg='white', bd=1, relief='solid')
        self.box_canvas.grid(row=0, column=1, padx=5, pady=5, sticky='w')
        self.box_canvas.bind("<Button-1>", lambda event: self.update_color_label(self.box_color_var, self.box_canvas))

        Label(box_frame, text="Box Opacity:").grid(row=0, column=2, padx=5, pady=5, sticky='w')
        self.scale_box_opacity = Scale(box_frame, from_=0, to=100, orient=tk.HORIZONTAL, length=150, command=lambda value: self.update_sample_text())
        self.scale_box_opacity.grid(row=0, column=3, padx=5, pady=5, sticky='w')

        slogan_frame = tk.Frame(content_frame)
        slogan_frame.grid(row=6, column=0, columnspan=4, padx=5, pady=5, sticky='we')

        Label(slogan_frame, text="TEXT TO ADD:").grid(row=0, column=0, padx=5, pady=5, sticky='ne')
        self.entry_slogan = tk.Text(slogan_frame, width=60, height=3)
        self.entry_slogan.grid(row=0, column=1, padx=5, pady=5, sticky='w')
        self.entry_slogan.bind("<KeyRelease>", lambda event: self.update_sample_text())

        self.var_transparency = IntVar()
        Checkbutton(content_frame, text="Transparency", variable=self.var_transparency).grid(row=7, column=0, padx=5, pady=5, sticky='w')

        Label(box_frame, text="WIDTH").grid(row=0, column=4, padx=5, pady=5, sticky='w')
        self.scale_box_width = Scale(box_frame, from_=0, to=100, orient=tk.HORIZONTAL, length=150, command=lambda value: self.update_sample_text())
        self.scale_box_width.grid(row=0, column=5, padx=5, pady=5, sticky='w')

        Button(content_frame, text="SAVE", command=self.on_save).grid(row=7, column=2, padx=5, pady=5, sticky='we')
        Button(content_frame, text="COPY", command=self.copy_to_clipboard_method).grid(row=7, column=3, padx=5, pady=5, sticky='we')
        Button(content_frame, text="Reload", command=self.reload_image).grid(row=1, column=3, padx=5, pady=5, sticky='w')

    def select_image(self):
        initial_dir = os.path.dirname(self.entry_image_path.get()) if self.entry_image_path.get() else './IMAGES'
        filename = filedialog.askopenfilename(initialdir=initial_dir, title="Select Image", filetypes=[("Image Files", "*.png *.jpg *.jpeg")])
        if filename:
            self.entry_image_path.delete(0, tk.END)
            self.entry_image_path.insert(0, normalize_path(filename))
            self.load_image(filename)
            self.update_sample_text()

    def load_image(self, image_path):
        try:
            image_path = normalize_path(image_path)
            if os.path.exists(image_path):
                self.image = Image.open(image_path).convert("RGBA")
                self.update_image_label()
                self.update_sample_text()
            else:
                print(f"Invalid image path: {image_path}")
                self.image = Image.new('RGBA', (300, 300), (200, 200, 200, 255))  # Create a gray placeholder
                self.update_image_label()
        except Exception as e:
            print(f"Error loading image: {e}")
            self.image = Image.new('RGBA', (300, 300), (200, 200, 200, 255))  # Create a gray placeholder
            self.update_image_label()
        
    def set_output_folder(self):
        initial_dir = self.entry_output_folder.get() or os.path.expanduser("~")
        folder = filedialog.askdirectory(initialdir=initial_dir, title="Select Folder")
        if folder:
            self.entry_output_folder.delete(0, tk.END)
            self.entry_output_folder.insert(0, folder)

    def update_sample_text(self):
        if self.image:
            slogan = self.entry_slogan.get("1.0", "end-1c")
            font_size = self.scale_font_size.get()
            font_thickness = self.scale_font_thickness.get()
            font_color = self.color_var.get() or '255,255,255'
            outline_color = self.outline_color_var.get() or '0,0,0'
            outline_thickness = self.scale_outline_thickness.get() + 2 if self.scale_outline_thickness.get() > 0 else 0
            box_color = self.box_color_var.get() or '0,0,0'
            box_opacity = self.scale_box_opacity.get() / 100.0
            use_box = box_opacity > 0
            text_position = self.scale_text_position.get()
            box_width = self.scale_box_width.get()

            updated_image = self.add_slogan_to_image(self.image, slogan, font_color, font_thickness, font_size, outline_color, outline_thickness, box_color, box_opacity, use_box, text_position, box_width)
            if updated_image:
                if self.var_transparency.get() == 1:
                    updated_image = self.make_transparent(updated_image)
                updated_image = self.resize_image(updated_image, 300, 300)
                self.updated_image = ImageTk.PhotoImage(updated_image)
                self.img_label.config(image=self.updated_image)
                self.img_label.image = self.updated_image
            else:
                print("Failed to update image with settings")

    def make_transparent(self, image):
        data = np.array(image)
        alpha = data[:,:,3]
        rgb = data[:,:,:3]
        
        # Make white background transparent
        mask = (rgb == [255, 255, 255]).all(axis=2)
        alpha[mask] = 0
        
        return Image.fromarray(np.concatenate([rgb, alpha.reshape(*alpha.shape, 1)], axis=2))
                
    def apply_polaroid(self):
        if self.image:
            self.image = create_polaroid(self.image)
            self.update_image_label()
            self.update_sample_text()
        
    def update_color_label(self, var, canvas):
        color_rgb, color_hex = colorchooser.askcolor(title="Choose Color")
        print(f"update_color_label called with: color_rgb={color_rgb}, color_hex={color_hex}")
        if color_rgb is not None and color_hex is not None:
            color_rgb_str = f"{int(color_rgb[0])},{int(color_rgb[1])},{int(color_rgb[2])}"
            var.set(color_rgb_str)
            print(f"Updated color variable: var={var.get()}")
            canvas.config(bg=color_hex)
        else:
            print("No color selected, keeping previous color")
        self.update_sample_text()
    
    def save_settings(self):
        x = self.root.winfo_x()
        y = self.root.winfo_y()
        config = {
            'font_size': self.scale_font_size.get(),
            'font_thickness': self.scale_font_thickness.get(),
            'outline_thickness': self.scale_outline_thickness.get() + 2,
            'font_color': self.color_var.get() or '255,255,255',
            'outline_color': self.outline_color_var.get() or '0,0,0',
            'box_color': self.box_color_var.get() or '0,0,0',
            'box_opacity': self.scale_box_opacity.get(),
            'box_width': self.scale_box_width.get(),
            'use_box': self.scale_box_opacity.get() > 0,
            'output_folder': normalize_path(self.entry_output_folder.get()),
            'text_position': self.scale_text_position.get(),
            'image_path': normalize_path(os.path.relpath(self.entry_image_path.get(), os.path.dirname(os.path.abspath(__file__)))),
            'on_top': self.on_top.get(),
            'window_position': [x, y],
            'transparency': self.var_transparency.get(),
            'slogan': self.entry_slogan.get("1.0", "end-1c"),
        }
        print(f"Saving settings: {config}")
        self.save_config(config)

    def load_settings(self):
        config = self.load_config()
        if config:
            print(f"Loaded settings: {config}")
            self.scale_font_size.set(config.get('font_size', 1))
            self.scale_font_thickness.set(config.get('font_thickness', 1))
            self.scale_outline_thickness.set(config.get('outline_thickness', 3) - 2)
            self.color_var.set(config.get('font_color', '255,255,255'))
            self.outline_color_var.set(config.get('outline_color', '0,0,0'))
            self.box_color_var.set(config.get('box_color', '0,0,0'))
            self.scale_box_opacity.set(config.get('box_opacity', 0))
            self.scale_box_width.set(config.get('box_width', 50))
            self.entry_output_folder.delete(0, tk.END)
            self.entry_output_folder.insert(0, normalize_path(config.get('output_folder', '')))
            self.scale_text_position.set(config.get('text_position', 0))
            self.entry_image_path.delete(0, tk.END)
            image_path = config.get('image_path', EXAMPLE_IMAGE)
            if not os.path.isabs(image_path):
                image_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), image_path)
            full_image_path = normalize_path(os.path.abspath(image_path))
            self.entry_image_path.insert(0, full_image_path)
            self.on_top.set(config.get('on_top', 0))
            if self.on_top.get():
                self.root.attributes('-topmost', True)
            window_position = config.get('window_position', None)
            if window_position:
                self.root.geometry(f"+{window_position[0]}+{window_position[1]}")
            self.var_transparency.set(config.get('transparency', 0))
            self.load_image(full_image_path)
            self.entry_slogan.delete("1.0", tk.END)
            self.entry_slogan.insert("1.0", config.get('slogan', ''))
            self.update_canvas_colors()
            self.update_sample_text()
        else:
            print("No settings file found. Loading defaults.")
            self.load_default_settings()

    def load_default_settings(self):
        self.scale_font_size.set(1)
        self.scale_font_thickness.set(1)
        self.scale_outline_thickness.set(1)
        self.color_var.set('255,255,255')
        self.outline_color_var.set('0,0,0')
        self.box_color_var.set('0,0,0')
        self.scale_box_opacity.set(0)
        self.scale_box_width.set(50)
        default_output_folder = os.path.join(os.path.expanduser("~"), "Pictures", "MemePic")
        self.entry_output_folder.delete(0, tk.END)
        self.entry_output_folder.insert(0, normalize_path(default_output_folder))
        self.scale_text_position.set(0)
        self.entry_image_path.delete(0, tk.END)
        full_image_path = normalize_path(os.path.abspath(os.path.join(os.path.dirname(__file__), EXAMPLE_IMAGE)))
        self.entry_image_path.insert(0, full_image_path)
        self.on_top.set(0)
        self.var_transparency.set(0)
        self.load_image(full_image_path)
        self.update_canvas_colors()
    
    def update_canvas_colors(self):
        font_color = self.color_var.get() or '255,255,255'
        outline_color = self.outline_color_var.get() or '0,0,0'
        box_color = self.box_color_var.get() or '0,0,0'

        self.update_color_canvas(self.color_canvas, font_color)
        self.update_color_canvas(self.outline_canvas, outline_color)
        self.update_color_canvas(self.box_canvas, box_color)
        
    def update_color_canvas(self, canvas, color_str):
        color_rgb = tuple(map(int, color_str.split(',')))
        color_hex = f'#{color_rgb[0]:02x}{color_rgb[1]:02x}{color_rgb[2]:02x}'
        canvas.config(bg=color_hex, bd=1, relief='solid')

    def show_about(self):
        about_text = "MEM PIC\n\nVersion: 1.0\n\nFor more information, visit:\nhttps://github.com/Tolerable/MEMEPIC/\n\nDeveloped by: Your Name\n\nDate: 2024"
        messagebox.showinfo("About MEM PIC", about_text)

if __name__ == "__main__":
    root = tk.Tk()
    app = MEMEPICApp(root)
    root.mainloop()
