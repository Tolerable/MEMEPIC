import os
import cv2
import tkinter as tk
from tkinter import filedialog, colorchooser, ttk, IntVar, StringVar, Checkbutton, Entry, Label, Button

def convert_to_bgr(color):
    if color:  # Ensure the color is not None
        return (int(color[2]), int(color[1]), int(color[0]))
    return None

def update_color_label(label, var):
    color_rgb, color_hex = colorchooser.askcolor(title="Choose Color")
    if color_rgb:
        # Store the color as a string in the format 'B,G,R'
        color_bgr_str = f"{int(color_rgb[2])},{int(color_rgb[1])},{int(color_rgb[0])}"
        var.set(color_bgr_str)
        label.config(text=color_hex)  # Display the hex color
    else:
        var.set('')  # Set to empty string if no color is chosen
        label.config(text='No color selected')

def add_slogan_to_image(image_path, slogan_text, font_color_str, font_thickness, font_scale, outline_color_str, use_outline, box_color_str, box_opacity):
    image = cv2.imread(image_path)
    if image is None:
        print("Image not found or unable to open.")
        return None

    font = cv2.FONT_HERSHEY_SIMPLEX
    image_width, image_height = image.shape[1], image.shape[0]

    # Dynamically adjust font size to fit the slogan within the image width
    while True:
        text_size, baseline = cv2.getTextSize(slogan_text, font, font_scale, int(font_thickness))
        text_width, text_height = text_size

        # Break the loop if the text fits within the image width or if the font size is too small
        if text_width <= image_width or font_scale <= 0.5:
            break
        font_scale -= 0.1  # Decrease font size and check again

    # Calculate text position (horizontally centered, near the bottom)
    text_x = (image_width - text_width) // 2
    text_y = image_height - text_height - baseline - 10  # 10 pixels above the bottom

    # Adjust box position and size
    padding = 10
    rect_top_left = (text_x - padding, text_y - text_height - baseline - padding)
    rect_bottom_right = (text_x + text_width + padding, text_y + baseline + padding)

    # Parse color strings
    font_color = tuple(map(int, font_color_str.split(','))) if font_color_str else (255, 255, 255)
    box_color = tuple(map(int, box_color_str.split(','))) if box_color_str else (0, 0, 0)
    outline_color = tuple(map(int, outline_color_str.split(','))) if outline_color_str and use_outline else None

    # Draw background box
    overlay = image.copy()
    cv2.rectangle(overlay, rect_top_left, rect_bottom_right, box_color, -1)
    cv2.addWeighted(overlay, box_opacity, image, 1 - box_opacity, 0, image)

    # Draw text outline
    if use_outline:
        cv2.putText(image, slogan_text, (text_x, text_y), font, font_scale, outline_color, font_thickness + 2)

    # Draw main text
    cv2.putText(image, slogan_text, (text_x, text_y), font, font_scale, font_color, font_thickness)

    # Save the new image
    new_image_path = os.path.splitext(image_path)[0] + '_sloganed.png'
    cv2.imwrite(new_image_path, image)

    return new_image_path


def create_gui():
    def on_submit():
        # Retrieve values from the GUI
        image_path = entry_image_path.get()
        slogan = entry_slogan.get()
        font_size = float(combo_font_size.get())
        font_thickness = int(combo_font_thickness.get())
        font_color = color_var.get()
        outline_color = outline_color_var.get()
        use_outline = var_use_outline.get() == 1
        box_color = box_color_var.get()
        box_opacity = float(entry_box_opacity.get())

        new_image_path = add_slogan_to_image(image_path, slogan, font_color, font_thickness, font_size, outline_color, use_outline, box_color, box_opacity)
        print(f"Slogan added to image. New image saved at {new_image_path}")
        root.destroy()

    def select_image():
        filename = filedialog.askopenfilename(initialdir='./IMAGES', title="Select Image", filetypes=[("Image Files", "*.png *.jpg *.jpeg")])
        entry_image_path.delete(0, tk.END)
        entry_image_path.insert(0, filename)

    root = tk.Tk()
    root.title("Image Slogan Customization")

    entry_image_path = Entry(root, width=50)
    entry_image_path.grid(row=0, column=1)
    Button(root, text="Select Image", command=select_image).grid(row=0, column=2)

    Label(root, text="Slogan:").grid(row=1, column=0)
    entry_slogan = Entry(root, width=50)
    entry_slogan.grid(row=1, column=1)

    Label(root, text="Font Size:").grid(row=2, column=0)
    combo_font_size = ttk.Combobox(root, values=[1, 2, 3, 4, 5], width=4)
    combo_font_size.grid(row=2, column=1)
    combo_font_size.set(1)

    Label(root, text="Font Thickness:").grid(row=3, column=0)
    combo_font_thickness = ttk.Combobox(root, values=[1, 2, 3, 4, 5], width=4)
    combo_font_thickness.grid(row=3, column=1)
    combo_font_thickness.set(1)

    color_var = StringVar()
    color_label = Label(root, text='(0, 0, 0)')
    color_label.grid(row=4, column=1)
    Button(root, text="Select Font Color", command=lambda: update_color_label(color_label, color_var)).grid(row=4, column=0)

    outline_color_var = StringVar()
    outline_color_label = Label(root, text='(0, 0, 0)')
    outline_color_label.grid(row=5, column=1)
    Button(root, text="Select Outline Color", command=lambda: update_color_label(outline_color_label, outline_color_var)).grid(row=5, column=0)

    var_use_outline = IntVar()
    Checkbutton(root, text="Use Outline", variable=var_use_outline).grid(row=6, column=0)

    box_color_var = StringVar()
    box_color_label = Label(root, text='(255, 255, 255)')
    box_color_label.grid(row=7, column=1)
    Button(root, text="Select Box Color", command=lambda: update_color_label(box_color_label, box_color_var)).grid(row=7, column=0)

    Label(root, text="Box Opacity:").grid(row=8, column=0)
    entry_box_opacity = Entry(root, width=4)
    entry_box_opacity.grid(row=8, column=1)
    entry_box_opacity.insert(0, "0.5")

    Button(root, text="Submit", command=on_submit).grid(row=9, column=1)

    root.mainloop()

def main():
    create_gui()

if __name__ == "__main__":
    main()
