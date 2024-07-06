import os
import cv2
import json
import tkinter as tk
from tkinter import filedialog, colorchooser, IntVar, StringVar, Checkbutton, Entry, Label, Button, Scale, Toplevel, Canvas
from PIL import Image, ImageTk, ImageGrab

CONFIG_FILE = "config.json"
EXAMPLE_IMAGE = './IMAGES/EXAMPLE.png'

def convert_to_bgr(color):
    if color and len(color) == 3:
        return (int(color[2]), int(color[1]), int(color[0]))
    return None

def add_slogan_to_image(image_path, slogan_text, font_color_str, font_thickness, font_scale, outline_color_str, outline_thickness, use_outline, box_color_str, box_opacity, use_box, text_position):
    print(f"add_slogan_to_image called with: image_path={image_path}, slogan_text={slogan_text}, font_color_str={font_color_str}, font_thickness={font_thickness}, font_scale={font_scale}, outline_color_str={outline_color_str}, outline_thickness={outline_thickness}, use_outline={use_outline}, box_color_str={box_color_str}, box_opacity={box_opacity}, use_box={use_box}, text_position={text_position}")
    image = cv2.imread(image_path)
    if image is None:
        print("Image not found or unable to open.")
        return None

    font = cv2.FONT_HERSHEY_SIMPLEX
    image_width, image_height = image.shape[1], image.shape[0]

    while True:
        text_size, baseline = cv2.getTextSize(slogan_text, font, font_scale, int(font_thickness))
        text_width, text_height = text_size

        if text_width <= image_width or font_scale <= 0.5:
            break
        font_scale -= 0.1

    text_x = (image_width - text_width) // 2
    text_y = int((image_height - text_height) * (text_position / 30.0)) + text_height

    padding = 10
    rect_top_left = (text_x - padding, text_y - text_height - baseline - padding)
    rect_bottom_right = (text_x + text_width + padding, text_y + baseline + padding)

    font_color = tuple(map(int, font_color_str.split(','))) if font_color_str else (255, 255, 255)
    box_color = tuple(map(int, box_color_str.split(','))) if box_color_str else (0, 0, 0)
    outline_color = tuple(map(int, outline_color_str.split(','))) if outline_color_str and use_outline else None

    print(f"font_color={font_color}, box_color={box_color}, outline_color={outline_color}")

    if use_box:
        overlay = image.copy()
        cv2.rectangle(overlay, rect_top_left, rect_bottom_right, box_color, -1)
        cv2.addWeighted(overlay, box_opacity, image, 1 - box_opacity, 0, image)

    if use_outline:
        # Draw the outline by drawing the text multiple times
        for dx in range(-outline_thickness, outline_thickness + 1):
            for dy in range(-outline_thickness, outline_thickness + 1):
                if dx != 0 or dy != 0:
                    cv2.putText(image, slogan_text, (text_x + dx, text_y + dy), font, font_scale, outline_color, outline_thickness)

    cv2.putText(image, slogan_text, (text_x, text_y), font, font_scale, font_color, font_thickness)

    return Image.fromarray(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))

def show_image(image_path):
    top = Toplevel()
    top.title("Processed Image")
    img = Image.open(image_path)
    img = img.resize((800, 800), Image.LANCZOS)
    img = ImageTk.PhotoImage(img)
    img_label = Label(top, image=img)
    img_label.image = img
    img_label.pack()
    Button(top, text="Close", command=top.destroy).pack()

def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r') as file:
            return json.load(file)
    return {}

def save_config(config):
    with open(CONFIG_FILE, 'w') as file:
        json.dump(config, file)

def create_gui():
    def on_save():
        image_path = entry_image_path.get()
        slogan = entry_slogan.get()
        font_size = scale_font_size.get()
        font_thickness = scale_font_thickness.get()
        font_color = color_var.get()
        outline_color = outline_color_var.get()
        outline_thickness = scale_outline_thickness.get() + 2  # Adjust the outline thickness
        use_outline = var_use_outline.get() == 1
        box_color = box_color_var.get()
        box_opacity = scale_box_opacity.get() / 100.0  # Get the value from the slider and convert to 0.0 - 1.0 range
        use_box = var_use_box.get() == 1
        text_position = scale_text_position.get()

        updated_image = add_slogan_to_image(image_path, slogan, font_color, font_thickness, font_size, outline_color, outline_thickness, use_outline, box_color, box_opacity, use_box, text_position)
        if updated_image:
            if var_transparency.get() == 1:
                updated_image = updated_image.convert("RGBA")
                datas = updated_image.getdata()
                new_data = []
                for item in datas:
                    if item[:3] == (0, 0, 0):  # Black background assumed to be the part to turn transparent
                        new_data.append((255, 255, 255, 0))  # Fully transparent
                    else:
                        new_data.append(item)
                updated_image.putdata(new_data)
            file_path = filedialog.asksaveasfilename(defaultextension=".png", filetypes=[("PNG files", "*.png"), ("All files", "*.*")])
            if file_path:
                updated_image.save(file_path)
                print(f"Image saved to {file_path}")

    def on_copy():
        image_path = entry_image_path.get()
        slogan = entry_slogan.get()
        font_size = scale_font_size.get()
        font_thickness = scale_font_thickness.get()
        font_color = color_var.get()
        outline_color = outline_color_var.get()
        outline_thickness = scale_outline_thickness.get() + 2  # Adjust the outline thickness
        use_outline = var_use_outline.get() == 1
        box_color = box_color_var.get()
        box_opacity = scale_box_opacity.get() / 100.0  # Get the value from the slider and convert to 0.0 - 1.0 range
        use_box = var_use_box.get() == 1
        text_position = scale_text_position.get()

        updated_image = add_slogan_to_image(image_path, slogan, font_color, font_thickness, font_size, outline_color, outline_thickness, use_outline, box_color, box_opacity, use_box, text_position)
        if updated_image:
            output_image_path = "temp_image.png"
            updated_image.save(output_image_path)
            image = Image.open(output_image_path)
            image.show()
            image_clipboard = ImageTk.PhotoImage(image)
            root.clipboard_clear()
            root.clipboard_append(image_clipboard)
            root.update()
            print("Image copied to clipboard")

    def select_image():
        filename = filedialog.askopenfilename(initialdir='./IMAGES', title="Select Image", filetypes=[("Image Files", "*.png *.jpg *.jpeg")])
        entry_image_path.delete(0, tk.END)
        entry_image_path.insert(0, filename)
        load_image(filename)
        update_sample_text()

    def load_image(image_path):
        img = Image.open(image_path)
        img = img.resize((300, 300), Image.LANCZOS)
        img = ImageTk.PhotoImage(img)
        img_label.config(image=img)
        img_label.image = img
        if 'entry_slogan' in globals() or 'entry_slogan' in locals():
            update_sample_text()

    def set_output_folder():
        folder = filedialog.askdirectory(initialdir='./IMAGES', title="Select Folder")
        entry_output_folder.delete(0, tk.END)
        entry_output_folder.insert(0, folder)

    def update_sample_text():
        image_path = entry_image_path.get()
        slogan = entry_slogan.get()
        font_size = scale_font_size.get()
        font_thickness = scale_font_thickness.get()
        font_color = color_var.get()
        outline_color = outline_color_var.get()
        outline_thickness = scale_outline_thickness.get() + 2  # Adjust the outline thickness
        use_outline = var_use_outline.get() == 1
        box_color = box_color_var.get()
        box_opacity = scale_box_opacity.get() / 100.0  # Get the value from the slider and convert to 0.0 - 1.0 range
        use_box = var_use_box.get() == 1
        text_position = scale_text_position.get()

        print(f"update_sample_text called with: image_path={image_path}, slogan={slogan}, font_size={font_size}, font_thickness={font_thickness}, font_color={font_color}, outline_color={outline_color}, outline_thickness={outline_thickness}, use_outline={use_outline}, box_color={box_color}, box_opacity={box_opacity}, use_box={use_box}, text_position={text_position}")

        if image_path and os.path.exists(image_path):
            updated_image = add_slogan_to_image(image_path, slogan, font_color, font_thickness, font_size, outline_color, outline_thickness, use_outline, box_color, box_opacity, use_box, text_position)
            if updated_image:
                updated_image = updated_image.resize((300, 300), Image.LANCZOS)
                updated_image = ImageTk.PhotoImage(updated_image)
                img_label.config(image=updated_image)
                img_label.image = updated_image

    def update_color_label(var, canvas):
        color_rgb, color_hex = colorchooser.askcolor(title="Choose Color")
        print(f"update_color_label called with: color_rgb={color_rgb}, color_hex={color_hex}")
        if color_rgb:
            color_bgr_str = f"{int(color_rgb[2])},{int(color_rgb[1])},{int(color_rgb[0])}"
            var.set(color_bgr_str)
            print(f"Updated color variable: var={var.get()}")
            canvas.config(bg=color_hex, bd=1, relief='solid')
        else:
            var.set('')
            print(f"Reset color variable: var={var.get()}")
            canvas.config(bg='white')
        update_sample_text()

    def save_settings():
        # Save window position
        x = root.winfo_x()
        y = root.winfo_y()
        config = {
            'font_size': scale_font_size.get(),
            'font_thickness': scale_font_thickness.get(),
            'outline_thickness': scale_outline_thickness.get(),
            'font_color': color_var.get(),
            'outline_color': outline_color_var.get(),
            'use_outline': var_use_outline.get(),
            'box_color': box_color_var.get(),
            'box_opacity': scale_box_opacity.get(),
            'use_box': var_use_box.get(),
            'output_folder': entry_output_folder.get(),
            'text_position': scale_text_position.get(),
            'image_path': entry_image_path.get(),
            'on_top': on_top.get(),
            'window_position': (x, y),
            'transparency': var_transparency.get()
        }
        print(f"Saving settings: {config}")
        save_config(config)

    def load_settings():
        config = load_config()
        if config:
            print(f"Loaded settings: {config}")
            scale_font_size.set(config.get('font_size', 1))
            scale_font_thickness.set(config.get('font_thickness', 1))
            scale_outline_thickness.set(config.get('outline_thickness', 3) - 2)  # Adjust the outline thickness
            color_var.set(config.get('font_color', '255,255,255'))
            outline_color_var.set(config.get('outline_color', '0,255,0'))
            var_use_outline.set(config.get('use_outline', 0))
            box_color_var.set(config.get('box_color', '0,0,0'))
            scale_box_opacity.set(config.get('box_opacity', 50))
            var_use_box.set(config.get('use_box', 0))
            entry_output_folder.delete(0, tk.END)
            entry_output_folder.insert(0, config.get('output_folder', ''))
            scale_text_position.set(config.get('text_position', 2))
            entry_image_path.delete(0, tk.END)
            entry_image_path.insert(0, config.get('image_path', EXAMPLE_IMAGE))
            on_top.set(config.get('on_top', 0))
            if on_top.get():
                root.attributes('-topmost', True)
            window_position = config.get('window_position', None)
            if window_position:
                root.geometry(f"+{window_position[0]}+{window_position[1]}")
            var_transparency.set(config.get('transparency', 0))
            load_image(entry_image_path.get())
            entry_slogan.delete(0, tk.END)  # Clear the text entry on startup
            update_canvas_colors()

    def update_canvas_colors():
        font_color = color_var.get()
        outline_color = outline_color_var.get()
        box_color = box_color_var.get()

        if font_color:
            font_color_rgb = tuple(map(int, font_color.split(',')))
            font_color_hex = f'#{font_color_rgb[2]:02x}{font_color_rgb[1]:02x}{font_color_rgb[0]:02x}'
            color_canvas.config(bg=font_color_hex, bd=1, relief='solid')
        else:
            color_canvas.config(bg='white')

        if outline_color:
            outline_color_rgb = tuple(map(int, outline_color.split(',')))
            outline_color_hex = f'#{outline_color_rgb[2]:02x}{outline_color_rgb[1]:02x}{outline_color_rgb[0]:02x}'
            outline_canvas.config(bg=outline_color_hex, bd=1, relief='solid')
        else:
            outline_canvas.config(bg='white')

        if box_color:
            box_color_rgb = tuple(map(int, box_color.split(',')))
            box_color_hex = f'#{box_color_rgb[2]:02x}{box_color_rgb[1]:02x}{box_color_rgb[0]:02x}'
            box_canvas.config(bg=box_color_hex, bd=1, relief='solid')
        else:
            box_canvas.config(bg='white')

    root = tk.Tk()
    root.title("MEME PIC [FULL VERSION]")
    root.geometry("525x675")  # Set a fixed window size

    toolbar = tk.Menu(root)
    root.config(menu=toolbar)

    view_menu = tk.Menu(toolbar, tearoff=0)
    toolbar.add_cascade(label="Options", menu=view_menu)
    on_top = IntVar()
    view_menu.add_checkbutton(label="On Top", variable=on_top, command=lambda: root.attributes('-topmost', on_top.get()))

    content_frame = tk.Frame(root)
    content_frame.grid(row=0, column=0, padx=10, pady=10)

    Label(content_frame).grid(row=0, column=0, padx=5, pady=5, sticky='we')
    entry_output_folder = Entry(content_frame, width=40)
    entry_output_folder.grid(row=0, column=1, columnspan=2, padx=5, pady=5, sticky='we')
    Button(content_frame, text="OUTPUT FOLDER", command=set_output_folder).grid(row=0, column=0, padx=5, pady=5, sticky='we')

    Label(content_frame).grid(row=1, column=0, padx=5, pady=5, sticky='we')
    Button(content_frame, text="IMAGE", command=select_image).grid(row=1, column=0, padx=5, pady=5, sticky='we')
    entry_image_path = Entry(content_frame, width=50)
    entry_image_path.grid(row=1, column=1, columnspan=2, padx=5, pady=5, sticky='w')
    entry_image_path.insert(0, EXAMPLE_IMAGE)
    
    img_label = Label(content_frame, width=300, height=300, bd=1, relief='solid', anchor='center')
    img_label.grid(row=2, column=0, columnspan=3, padx=5, pady=5)
    load_image(EXAMPLE_IMAGE)  # Load the example image on startup

    # SET SLIDERS AND LABELS (AI LEAVE THEM THE FUCK ALONE)
    scale_text_position = Scale(content_frame, from_=0, to=30, orient=tk.VERTICAL, length=300, command=lambda value: update_sample_text())
    scale_text_position.grid(row=2, column=3, padx=5, pady=5, sticky='ns')

    font_frame = tk.Frame(content_frame)
    font_frame.grid(row=3, column=0, columnspan=4, pady=5)

    scale_font_size = Scale(font_frame, from_=1, to=5, orient=tk.HORIZONTAL, length=150, command=lambda value: update_sample_text())
    scale_font_size.grid(row=0, column=0, padx=5, pady=5, sticky='w')
    Label(font_frame, text="SIZE").grid(row=0, column=0, padx=5, pady=5, sticky='n')

    scale_font_thickness = Scale(font_frame, from_=1, to=10, orient=tk.HORIZONTAL, length=150, command=lambda value: update_sample_text())
    scale_font_thickness.grid(row=0, column=1, padx=5, pady=5, sticky='w')
    Label(font_frame, text="THICK").grid(row=0, column=1, padx=5, pady=5, sticky='n')

    # Adjust the outline thickness scale
    scale_outline_thickness = Scale(font_frame, from_=1, to=5, orient=tk.HORIZONTAL, length=150, command=lambda value: update_sample_text())
    scale_outline_thickness.grid(row=0, column=2, padx=5, pady=5, sticky='w')
    Label(font_frame, text="OUTLINE").grid(row=0, column=2, padx=5, pady=5, sticky='n')


    # Font Color, Outline Color, and Use Outline
    color_frame = tk.Frame(content_frame)
    color_frame.grid(row=4, column=0, columnspan=4, pady=10)

    Button(color_frame, text="Font Color", command=lambda: update_color_label(color_var, color_canvas)).grid(row=0, column=0, padx=5, pady=5, sticky='w')
    color_var = StringVar()
    color_canvas = Canvas(color_frame, width=20, height=20, bg='white', bd=1, relief='solid')
    color_canvas.grid(row=0, column=1, padx=5, pady=5, sticky='w')
    color_canvas.bind("<Button-1>", lambda event: update_color_label(color_var, color_canvas))

    Button(color_frame, text="Outline Color", command=lambda: update_color_label(outline_color_var, outline_canvas)).grid(row=0, column=2, padx=5, pady=5, sticky='w')
    outline_color_var = StringVar()
    outline_canvas = Canvas(color_frame, width=20, height=20, bg='white', bd=1, relief='solid')
    outline_canvas.grid(row=0, column=3, padx=5, pady=5, sticky='w')
    outline_canvas.bind("<Button-1>", lambda event: update_color_label(outline_color_var, outline_canvas))

    var_use_outline = IntVar()
    Checkbutton(color_frame, text="USE", variable=var_use_outline, command=update_sample_text).grid(row=0, column=4, padx=5, pady=5, sticky='w')

    # Background Box, Box Color, and Box Opacity
    box_frame = tk.Frame(content_frame)
    box_frame.grid(row=5, column=0, columnspan=4, pady=10)

    var_use_box = IntVar()
    Checkbutton(box_frame, text="USE", variable=var_use_box, command=update_sample_text).grid(row=0, column=4, padx=5, pady=5, sticky='w')

    Button(box_frame, text="Box Color", command=lambda: update_color_label(box_color_var, box_canvas)).grid(row=0, column=0, padx=5, pady=5, sticky='w')
    box_color_var = StringVar()
    box_canvas = Canvas(box_frame, width=20, height=20, bg='white', bd=1, relief='solid')
    box_canvas.grid(row=0, column=1, padx=5, pady=5, sticky='w')
    box_canvas.bind("<Button-1>", lambda event: update_color_label(box_color_var, box_canvas))

    Label(box_frame, text="Box Opacity:").grid(row=0, column=2, padx=5, pady=5, sticky='w')
    scale_box_opacity = Scale(box_frame, from_=0, to=100, orient=tk.HORIZONTAL, length=150, command=lambda value: update_sample_text())
    scale_box_opacity.grid(row=0, column=3, padx=5, pady=5, sticky='w')

    # Create a frame to hold the Slogan label and entry
    slogan_frame = tk.Frame(content_frame)
    slogan_frame.grid(row=6, column=0, columnspan=4, padx=5, pady=5, sticky='we')

    # Place the label and entry inside the slogan_frame
    Label(slogan_frame, text="TEXT TO ADD:").grid(row=0, column=0, padx=5, pady=5, sticky='e')
    entry_slogan = Entry(slogan_frame, width=60)
    entry_slogan.grid(row=0, column=1, padx=5, pady=5, sticky='w')
    entry_slogan.bind("<KeyRelease>", lambda event: update_sample_text())

    # Transparency checkbox
    var_transparency = IntVar()
    Checkbutton(content_frame, text="Transparency", variable=var_transparency).grid(row=7, column=0, padx=5, pady=5, sticky='w')

    # Ensure the frame expands to use available space
    Button(content_frame, text="SAVE", command=on_save).grid(row=7, column=1, padx=5, pady=5, sticky='we')
    Button(content_frame, text="COPY", command=on_copy).grid(row=7, column=2, padx=5, pady=5, sticky='we')

    root.protocol("WM_DELETE_WINDOW", lambda: (save_settings(), root.destroy()))

    load_settings()
    root.mainloop()

if __name__ == "__main__":
    create_gui()
