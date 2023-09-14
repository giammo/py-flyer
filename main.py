import tkinter as tk
from tkinter import filedialog
from tkinter import ttk
from fpdf import FPDF

class ImageLayoutApp:
    def __init__(self, root):
        self.root = root
        self.root.title("App Layout Immagini")
        
        # Definizione delle variabili
        self.layout_var = tk.StringVar()
        self.layout_var.set("2x2")
        self.image_paths = [None] * 4  # 4 slots per le immagini

        # Frame principale
        main_frame = ttk.Frame(root)
        main_frame.pack(padx=20, pady=20)

        # Combobox per la scelta del layout
        layout_label = ttk.Label(main_frame, text="Scegli un layout:")
        layout_label.grid(row=0, column=0, sticky="w")

        layout_combobox = ttk.Combobox(main_frame, textvariable=self.layout_var, values=["2x2", "3x3", "4x4"])
        layout_combobox.grid(row=0, column=1, sticky="w")

        # Pulsante per aprire la finestra di modello
        open_model_button = ttk.Button(main_frame, text="Apri Finestra di Modello", command=self.open_model_window)
        open_model_button.grid(row=1, column=0, columnspan=2, pady=10)

    def open_model_window(self):
        layout = self.layout_var.get()
        if layout not in ["2x2", "3x3", "4x4"]:
            messagebox.showerror("Errore", "Seleziona un layout valido (2x2, 3x3, o 4x4).")
            return

        model_window = tk.Toplevel(self.root)
        model_window.title("Finestra di Modello")

        rows, cols = map(int, layout.split('x'))
        self.image_preview_frames = []

        for i in range(rows):
            for j in range(cols):
                frame = ttk.Frame(model_window, borderwidth=2, relief="solid")
                frame.grid(row=i, column=j, padx=10, pady=10)

                # Pulsante per caricare un'immagine
                load_image_button = ttk.Button(frame, text="Carica Immagine", command=lambda i=i, j=j: self.load_image(i, j))
                load_image_button.pack()

                self.image_preview_frames.append(frame)

        
        # Pulsante per generare il PDF
        generate_pdf_button = ttk.Button(model_window, text="Genera PDF", command=self.generate_pdf)
        generate_pdf_button.grid(row=rows, column=0, columnspan=cols, pady=10)


    def load_image(self, row, col):
        file_path = filedialog.askopenfilename(filetypes=[("Immagini", "*.jpg *.jpeg *.png *.gif")])
        if file_path:
            layout = self.layout_var.get()
            rows, cols = map(int, layout.split('x'))
            self.image_paths[row * cols + col] = file_path
            self.update_image_preview(row, col, file_path, cols)  # Passa 'cols' come argomento

    def update_image_preview(self, row, col, image_path, cols):
        frame = self.image_preview_frames[row * cols + col]
        preview_label = ttk.Label(frame, text="Anteprima:")
        preview_label.pack()

        image_preview = tk.PhotoImage(file=image_path)
        image_label = ttk.Label(frame, image=image_preview)
        image_label.image = image_preview  # Evita il garbage collection
        image_label.pack()


    def generate_pdf(self):
        layout = self.layout_var.get()
        rows, cols = map(int, layout.split('x'))
        pdf = FPDF()
        pdf.set_auto_page_break(auto=True, margin=15)

        for i in range(len(self.image_paths) // (rows * cols)):
            pdf.add_page()
            for r in range(rows):
                for c in range(cols):
                    index = i * (rows * cols) + r * cols + c
                    image_path = self.image_paths[index]
                    if image_path:
                        pdf.image(image_path, x=c * 90, y=r * 90 + 20, w=90)
                        pdf.set_font("Arial", size=12)
                        pdf.text(c * 90, r * 90 + 110, "Testo:")
                        pdf.text(c * 90, r * 90 + 130, "Prezzo:")

        pdf_file_name = "output.pdf"
        pdf.output(pdf_file_name)
        messagebox.showinfo("PDF Creato", f"PDF creato con successo come {pdf_file_name}.")

    def start(self):
        self.root.mainloop()

if __name__ == "__main__":
    root = tk.Tk()
    app = ImageLayoutApp(root)
    app.start()
