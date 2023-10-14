import tkinter as tk
from tkinter import filedialog
from tkinter import ttk
from fpdf import FPDF
from PIL import Image, ImageTk


class ImageLayoutApp:
	def __init__(self, root):
		self.root = root
		self.root.title("App Layout Immagini")
		self.root.minsize(800, 600)  # Imposta le dimensioni minime della finestra principale

		# Definizione delle variabili
		self.layout_var = tk.StringVar()
		self.layout_var.set("2x2")
		self.image_paths = [None] * 4  # 4 slots per le immagini
		self.secondary_windows = []

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
		open_model_button = ttk.Button(
			main_frame, text="Apri Finestra di Modello", command=self.open_model_window)
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

		self.icon_home = tk.PhotoImage(file="icon/home.png")
		self.icon_back = tk.PhotoImage(file="icon/back.png")

		rows, cols = map(int, layout.split('x'))
		self.image_preview_frames = []

		for i in range(rows):
			model_window.grid_rowconfigure(i, weight=1)
			for j in range(cols):
				model_window.grid_columnconfigure(j, weight=1)
				
				cell_frame = ttk.Frame(model_window, borderwidth=2, relief="solid")
				cell_frame.grid(row=i, column=j, padx=10, pady=10, sticky="nsew")
				
				# Configura la griglia interna del cell_frame
				cell_frame.grid_rowconfigure(0, weight=0)  # Peso 0 per il pulsante
				cell_frame.grid_rowconfigure(1, weight=1)  # Peso 1 per l'immagine
				cell_frame.grid_columnconfigure(0, weight=1)
				
				# Pulsante per caricare un'immagine
				load_image_button = ttk.Button(cell_frame, text="Carica Immagine", command=lambda i=i, j=j: self.load_image(i, j))
				load_image_button.grid(row=0, column=0, sticky="nsew")
				
				# Anteprima dell'immagine (inizialmente vuota)
				empty_image_label = ttk.Label(cell_frame)
				empty_image_label.grid(row=1, column=0, sticky="nsew")
				
				self.image_preview_frames.append((cell_frame, empty_image_label))  # Salviamo sia il frame che la label dell'anteprima

		# Pulsante per generare il PDF
		generate_pdf_button = ttk.Button(model_window, text="Genera PDF", command=self.generate_pdf)
		generate_pdf_button.grid(row=rows, column=0, columnspan=cols, pady=10)

		# Associa la funzione personalizzata all'evento di chiusura della finestra di modello
		model_window.protocol("WM_DELETE_WINDOW", lambda: self.on_model_window_close(model_window))
		
		self.secondary_windows.append(model_window)
		self.create_menu(model_window)
		self.create_icon_menu(model_window)


	def on_model_window_close(self, model_window):
		# Distruggi la finestra di modello
		model_window.destroy()
		
		# Rendi visibile la finestra principale
		self.root.deiconify()

				
	def load_image(self, row, col):
		file_paths = filedialog.askopenfilenames(filetypes=[("Immagini", "*.jpg *.jpeg *.png *.gif")])
		if file_paths:
			layout = self.layout_var.get()
			rows, cols = map(int, layout.split('x'))
			
			# Se sono state selezionate più immagini, inizia l'inserimento dalla prima cella
			if len(file_paths) > 1:
				row = col = 0
			
			# Calcola il numero di celle disponibili dalla posizione corrente in poi
			available_cells = rows * cols - (row * cols + col)
			
			# Limita il numero di immagini selezionate al numero di celle disponibili
			file_paths = file_paths[:available_cells]
			
			# Itera sui percorsi dei file selezionati e aggiorna le anteprime delle immagini
			for i, file_path in enumerate(file_paths):
				index = row * cols + col + i
				if index < len(self.image_paths):  # Verifica che l'indice sia valido
					self.image_paths[index] = file_path
					self.update_image_preview(row, col + i, file_path, cols)



	def update_image_preview(self, row, col, image_path, cols):
		button_frame, preview_frame = self.image_preview_frames[row * cols + col]
		
		# Trova l'eventuale label dell'anteprima dell'immagine esistente
		image_label = None
		for widget in preview_frame.winfo_children():
			if isinstance(widget, ttk.Label) and hasattr(widget, 'image'):
				image_label = widget
				break
		
		# Carica la nuova immagine
		original_image = Image.open(image_path)
		
		# Calcola le nuove dimensioni mantenendo l'aspect ratio
		base_width = preview_frame.winfo_width()  # Larghezza desiderata dell'anteprima
		w_percent = base_width / float(original_image.width)
		h_size = int(float(original_image.height) * float(w_percent))
		
		# Ridimensiona l'immagine
		resized_image = original_image.resize((base_width, h_size), Image.LANCZOS)
		
		image_preview = ImageTk.PhotoImage(resized_image)
		
		if image_label:
			# Aggiorna l'immagine del label esistente
			image_label.configure(image=image_preview)
			image_label.image = image_preview
		else:
			# Crea un nuovo label per l'anteprima dell'immagine
			image_label = ttk.Label(preview_frame, image=image_preview)
			image_label.image = image_preview
			image_label.pack()
		
		# Salva l'immagine originale PIL nel label
		image_label.original_image = original_image

	def create_icon_menu(self, window):
		icon_menu_frame = ttk.Frame(window, height=10)
		icon_menu_frame.grid(row=0, column=0, columnspan=2, sticky="ew")  # Usiamo grid invece di pack

		home_button = ttk.Label(icon_menu_frame, image=self.icon_home, cursor="hand2")
		home_button.grid(row=0, column=0, padx=2)
		home_button.bind("<Button-1>", lambda e: self.show_main_frame())

		back_button = ttk.Label(icon_menu_frame, image=self.icon_back, cursor="hand2")
		back_button.grid(row=0, column=1, padx=2)
		back_button.bind("<Button-1>", lambda e: self.show_previous_frame())

		# Configura la propagazione dei pesi dei widget
		window.grid_rowconfigure(0, weight=0)  # Riga 0 (menu icone) con peso 0
		window.grid_columnconfigure(0, weight=1)  # Colonna 0 con peso 1
		window.grid_columnconfigure(1, weight=1)  # Colonna 1 con peso 1

	def create_menu(self, window):
		menu_bar = tk.Menu(window)
		window.config(menu=menu_bar)
		
		navigate_menu = tk.Menu(menu_bar, tearoff=0)
		menu_bar.add_cascade(label="Navigazione", menu=navigate_menu)
		
		navigate_menu.add_command(label="Torna al Frame Principale", command=self.show_main_frame)
		navigate_menu.add_command(label="Torna al Frame Precedente", command=self.show_previous_frame)

	def show_main_frame(self):
		# Chiudi tutte le finestre secondarie e mostra la finestra principale
		self.root.deiconify()
		for win in self.secondary_windows:
			win.destroy()
		self.secondary_windows = []

	def show_previous_frame(self):
		# Chiudi la finestra corrente e mostra la precedente, se esiste
		if self.secondary_windows:
			current_window = self.secondary_windows.pop()
			current_window.destroy()
			if self.secondary_windows:
				self.secondary_windows[-1].deiconify()
			else:
				self.root.deiconify()

	def resize_image_preview(self, row, col, cols):
		button_frame, preview_frame = self.image_preview_frames[row * cols + col]
		
		# Trova l'eventuale label dell'anteprima dell'immagine esistente
		image_label = None
		for widget in preview_frame.winfo_children():
			if isinstance(widget, ttk.Label) and hasattr(widget, 'image'):
				image_label = widget
				break
		
		if image_label:
			# Ottieni l'immagine originale
			image = image_label.original_image  # Utilizza l'immagine originale salvata
			
			# Ottieni le dimensioni del frame
			frame_width = preview_frame.winfo_width()
			frame_height = preview_frame.winfo_height()
			
			# Calcola le nuove dimensioni dell'immagine mantenendo l'aspect ratio
			img_ratio = image.width / image.height
			frame_ratio = frame_width / frame_height
			
			if img_ratio > frame_ratio:
				# L'immagine è più larga rispetto al frame
				base_width = frame_width
				base_height = int(frame_width / img_ratio)
			else:
				# L'immagine è più alta rispetto al frame
				base_height = frame_height
				base_width = int(frame_height * img_ratio)
			
			# Ridimensiona l'immagine con PIL
			resized_image = image.resize((base_width, base_height), Image.LANCZOS)
			
			# Converte l'immagine ridimensionata in PhotoImage
			image_preview = ImageTk.PhotoImage(resized_image)
			
			# Aggiorna l'immagine del label
			image_label.configure(image=image_preview)
			image_label.image = image_preview  # Salva il riferimento all'oggetto PhotoImage


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
		messagebox.showinfo(
			"PDF Creato", f"PDF creato con successo come {pdf_file_name}.")

	def start(self):
		self.root.mainloop()


if __name__ == "__main__":
	root = tk.Tk()
	app = ImageLayoutApp(root)
	app.start()
