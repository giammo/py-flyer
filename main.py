import tkinter as tk
from tkinter import filedialog, ttk, messagebox
from fpdf import FPDF
from PIL import Image, ImageTk
import datetime
import threading
import webbrowser
import os

class ImageLayoutApp:
	def __init__(self, root):
		self.root = root
		self.root.title("App Layout Immagini")
		self.root.minsize(800, 600)  # Imposta le dimensioni minime della finestra principale

		self._resizing = False

		# Definizione delle variabili
		self.layout_var = tk.StringVar()
		self.layout_var.set("2x2")
		self.image_paths = [None] * 4  # 4 slots per le immagini
		self.secondary_windows = []  # Lista delle finestre secondarie aperte (finestra di modello)
		self.titles = {}  # Inizializza l'attributo titles come un dizionario vuoto
		self.prices = {}  # Inizializza l'attributo prices come un dizionario vuoto

		# Frame principale
		main_frame = ttk.Frame(root)
		main_frame.pack(padx=20, pady=20)

		# Combobox per la scelta del layout
		layout_label = ttk.Label(main_frame, text="Scegli un layout:")
		layout_label.grid(row=0, column=0, sticky="w")

		layout_combobox = ttk.Combobox(main_frame, textvariable=self.layout_var, values=["2x2", "3x3", "4x4"])
		layout_combobox.grid(row=0, column=1, sticky="w")

		# Calcola il numero massimo di righe e colonne dai modelli disponibili
		max_rows = max_cols = 0
		for layout in layout_combobox["values"]:
			rows, cols = map(int, layout.split('x'))
			max_rows = max(max_rows, rows)
			max_cols = max(max_cols, cols)

		# Inizializza la lista self.image_paths con una lunghezza sufficiente
		total_cells = max_rows * max_cols
		self.image_paths = [None] * total_cells

		# Pulsante per aprire la finestra di modello
		open_model_button = ttk.Button(main_frame, text="Apri Finestra di Modello", command=self.open_model_window)
		open_model_button.grid(row=1, column=0, columnspan=2, pady=10)


	def open_model_window(self):
		layout = self.layout_var.get()
		if layout not in ["2x2", "3x3", "4x4"]:
			messagebox.showerror("Errore", "Seleziona un layout valido (2x2, 3x3, o 4x4).")
			return

		self.root.withdraw()

		model_window = tk.Toplevel(self.root)
		model_window.title("Finestra di Modello")
		model_window.minsize(800, 600)
		model_window.geometry("800x600")
		model_window.resizable(True, True)

		self._last_model_window_size = (0, 0)  # (width, height)

		self.create_icon_menu(model_window)

		rows, cols = map(int, layout.split('x'))
		self.image_preview_frames = []

		for i in range(rows):
			model_window.grid_rowconfigure(i+1, weight=1)
			for j in range(cols):
				model_window.grid_columnconfigure(j, weight=1)

				cell_frame = ttk.Frame(model_window, borderwidth=2, relief="solid")
				cell_frame.grid(row=i+1, column=j, padx=10, pady=10, sticky="nsew")

				cell_frame.grid_rowconfigure(0, weight=0)
				cell_frame.grid_rowconfigure(1, weight=3)
				cell_frame.grid_rowconfigure(2, weight=1)
				cell_frame.grid_columnconfigure(0, weight=1)

				load_image_button = ttk.Button(cell_frame, text="Carica Immagine", command=lambda i=i, j=j: self.load_image(i, j))
				load_image_button.grid(row=0, column=0, sticky="nsew")

				empty_image_label = ttk.Label(cell_frame)
				empty_image_label.grid(row=1, column=0, sticky="nsew")

				self.image_preview_frames.append((cell_frame, empty_image_label))

		generate_pdf_button = ttk.Button(model_window, text="Genera PDF", command=self.generate_pdf)
		generate_pdf_button.grid(row=rows+1, column=0, columnspan=cols, pady=10)

		self.progress = ttk.Progressbar(model_window, orient="horizontal", length=300, mode="determinate")
		self.progress.grid(row=rows+2, column=0, columnspan=cols, pady=10)

		model_window.protocol("WM_DELETE_WINDOW", lambda: self.on_model_window_close(model_window))

		self.secondary_windows.append(model_window)
		self.create_menu(model_window)

	def on_model_window_close(self, model_window):
		model_window.destroy()
		self.root.deiconify()

	def load_image(self, row, col):
		file_paths = filedialog.askopenfilenames(filetypes=[("Immagini", "*.jpg *.jpeg *.png *.gif")])
		if file_paths:
			layout = self.layout_var.get()
			rows, cols = map(int, layout.split('x'))

			if len(file_paths) > 1:
				row = col = 0

			available_cells = rows * cols - (row * cols + col)
			file_paths = file_paths[:available_cells]

			for i, file_path in enumerate(file_paths):
				index = row * cols + col + i
				if index < len(self.image_paths):
					self.image_paths[index] = file_path
					self.update_image_preview(row, col + i, file_path, cols)

	def update_image_preview(self, row, col, image_path, cols):
		if image_path is None:
			return

		button_frame, preview_frame = self.image_preview_frames[row * cols + col]

		image_label = None
		for widget in preview_frame.winfo_children():
			if isinstance(widget, ttk.Label) and hasattr(widget, 'image'):
				image_label = widget
				break

		original_image = Image.open(image_path)

		resized_image = original_image.resize((100, 100), Image.LANCZOS)
		image_preview = ImageTk.PhotoImage(resized_image)

		if image_label:
			image_label.configure(image=image_preview)
			image_label.image = image_preview
		else:
			image_label = ttk.Label(preview_frame, image=image_preview)
			image_label.image = image_preview
			image_label.grid(row=1, column=0, columnspan=2, sticky="nsew")

		image_label.original_image = original_image

		preview_frame.grid_rowconfigure(1, weight=1)
		preview_frame.grid_rowconfigure(2, weight=0)

		preview_frame.grid_columnconfigure(0, weight=6)
		preview_frame.grid_columnconfigure(1, weight=4)

		title_entry = tk.Entry(preview_frame, fg='grey')
		title_entry.insert(0, "Titolo")
		title_entry.bind("<FocusIn>", lambda e: self.handle_placeholder(e, "Titolo"))
		title_entry.bind("<FocusOut>", lambda e: self.handle_placeholder(e, "Titolo"))
		title_entry.grid(row=2, column=0, sticky="ew", pady=5, padx=(0, 5))

		price_entry = tk.Entry(preview_frame, fg='grey')
		price_entry.insert(0, "Prezzo")
		price_entry.bind("<FocusIn>", lambda e: self.handle_placeholder(e, "Prezzo"))
		price_entry.bind("<FocusOut>", lambda e: self.handle_placeholder(e, "Prezzo"))
		price_entry.grid(row=2, column=1, sticky="ew", pady=5, padx=(5, 0))

		# Salva gli input di titolo e prezzo
		self.titles[row * cols + col] = title_entry
		self.prices[row * cols + col] = price_entry




	def handle_placeholder(self, event, placeholder_text):
		entry_widget = event.widget
		if entry_widget.get() == placeholder_text:
			entry_widget.delete(0, tk.END)
			entry_widget.config(fg='black')

	def create_icon_menu(self, window):
		icon_width = 30
		icon_height = 30

		original_icon_home = Image.open("icon/home.png").convert("RGBA")
		resized_icon_home = original_icon_home.resize((icon_width, icon_height), Image.LANCZOS)
		self.icon_home = ImageTk.PhotoImage(resized_icon_home)

		original_icon_back = Image.open("icon/back.png")
		resized_icon_back = original_icon_back.resize((icon_width, icon_height), Image.LANCZOS)
		self.icon_back = ImageTk.PhotoImage(resized_icon_back)

		icon_menu_frame = ttk.Frame(window, height=10)
		icon_menu_frame.grid(row=0, column=0, columnspan=2, sticky="ew")

		home_button = ttk.Label(icon_menu_frame, image=self.icon_home, cursor="hand2")
		home_button.grid(row=0, column=0, padx=2)
		home_button.bind("<Button-1>", lambda e: self.show_main_frame())

		back_button = ttk.Label(icon_menu_frame, image=self.icon_back, cursor="hand2")
		back_button.grid(row=0, column=1, padx=2)
		back_button.bind("<Button-1>", lambda e: self.show_previous_frame())

		window.grid_rowconfigure(0, weight=0)
		window.grid_columnconfigure(0, weight=1)
		window.grid_columnconfigure(1, weight=1)

	def create_menu(self, window):
		menu_bar = tk.Menu(window)
		window.config(menu=menu_bar)

		navigate_menu = tk.Menu(menu_bar, tearoff=0)
		menu_bar.add_cascade(label="Navigazione", menu=navigate_menu)

		navigate_menu.add_command(label="Torna al Frame Principale", command=self.show_main_frame)
		navigate_menu.add_command(label="Torna al Frame Precedente", command=self.show_previous_frame)

	def show_main_frame(self):
		self.root.deiconify()
		for win in self.secondary_windows:
			win.destroy()
		self.secondary_windows = []

	def show_previous_frame(self):
		if self.secondary_windows:
			current_window = self.secondary_windows.pop()
			current_window.destroy()
			if self.secondary_windows:
				self.secondary_windows[-1].deiconify()
			else:
				self.root.deiconify()


	def generate_pdf(self):
		
		total_images = sum(1 for path in self.image_paths if path)
		self.progress["value"] = 0
		self.progress["maximum"] = total_images

		def generate_pdf_worker():
			rows, cols = map(int, self.layout_var.get().split('x'))
			PADDING = 5  # padding in mm
			MARGIN = 15  # margine in mm
			CELL_HEIGHT = ((297 - 2 * MARGIN) / rows) - 2 * PADDING
			CELL_WIDTH = ((210 - 2 * MARGIN) / cols) - 2 * PADDING
			TEXT_AREA_HEIGHT = 15  # altezza in mm per l'area del testo
			IMAGE_AREA_HEIGHT = CELL_HEIGHT - TEXT_AREA_HEIGHT

			pdf_file_name = self.generate_pdf_filename()
			pdf = FPDF(format='A4')
			pdf.set_auto_page_break(auto=True, margin=MARGIN)

			for i in range(len(self.image_paths) // (rows * cols)):
				images_to_print = [img for img in self.image_paths[i*(rows*cols):(i+1)*(rows*cols)] if img]
				if not images_to_print:
					continue

				pdf.add_page()
				for r in range(rows):
					for c in range(cols):
						index = i * (rows * cols) + r * cols + c
						image_path = self.image_paths[index]

						if image_path:
							SPACING = 5  # spaziatura in mm tra le celle
							x = MARGIN + c * (CELL_WIDTH + SPACING) + PADDING
							y = MARGIN + r * (CELL_HEIGHT + SPACING) + PADDING

							# Mantieni l'aspect ratio
							img = Image.open(image_path)
							img_w, img_h = img.size
							aspect_ratio = img_w / img_h

							# Calcola le dimensioni basate sull'altezza
							new_w_h = IMAGE_AREA_HEIGHT * aspect_ratio
							new_h_h = IMAGE_AREA_HEIGHT

							# Calcola le dimensioni basate sulla larghezza
							new_w_w = CELL_WIDTH
							new_h_w = CELL_WIDTH / aspect_ratio

							# Utilizza le dimensioni più piccole
							if new_w_h <= CELL_WIDTH:
								new_w = new_w_h
								new_h = new_h_h
							else:
								new_w = new_w_w
								new_h = new_h_w

							# Calcola le coordinate x e y per centrare l'immagine nella cella
							x_centered = x + (CELL_WIDTH - new_w) / 2
							y_centered = y + (IMAGE_AREA_HEIGHT - new_h) / 2

							pdf.image(image_path, x=x_centered, y=y_centered, w=new_w, h=new_h)


							# Ottieni il titolo e il prezzo
							title = self.titles[r * cols + c].get()
							price = self.prices[r * cols + c].get()

							# Stampa il titolo e il prezzo
							pdf.set_font("Arial", size=12)
							text_y = y + IMAGE_AREA_HEIGHT + 5
							pdf.text(x, text_y, title)
							pdf.set_font("Arial", "B", size=12)  # Grassetto
							pdf.text(x + pdf.get_string_width(title) + 5, text_y, price)
							
							# Aggiorna la barra di progresso
							self.progress["value"] += 1
							self.root.update()  # Questo aggiorna la GUI e fa avanzare la barra di progresso


			pdf.output(pdf_file_name)
			result = messagebox.askyesno("PDF Creato", f"PDF creato come {pdf_file_name}.\nVuoi aprirlo?")
			if result:
				webbrowser.open(pdf_file_name)
			
			# Azzera la barra di progresso
			self.progress["value"] = 0
			self.root.update()  # Questo aggiorna la GUI e azzera la barra di progresso


		pdf_thread = threading.Thread(target=generate_pdf_worker)
		pdf_thread.start()



	def generate_pdf_filename(self):
		now = datetime.datetime.now()
		timestamp = now.strftime("%Y-%m-%d_%H-%M-%S")
		layout = self.layout_var.get()
		pdf_folder = "pdf"  # Nome della cartella in cui salvare il PDF
		pdf_filename = f"{timestamp}_{layout}_output.pdf"
		pdf_path = os.path.join(pdf_folder, pdf_filename)  # Unisci il percorso della cartella e il nome del file
		return pdf_path

	def start(self):
		self.root.mainloop()

if __name__ == "__main__":
	root = tk.Tk()
	app = ImageLayoutApp(root)
	app.start()
