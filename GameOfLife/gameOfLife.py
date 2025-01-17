import customtkinter as ctk
from tkinter import Canvas, colorchooser, messagebox
import random
import json
import pygame

def play_sound_in_thread(sound_file):
    sound = pygame.mixer.Sound(sound_file)
    sound.play()

class GameOfLife:
    """
    A class to represent the Game of Life.

    Attributes:
    frame : tkinter.Frame
        The frame in which the game is displayed.
    app : tkinter.Tk
        The main application instance.
    rows : int
        The number of rows in the grid.
    cols : int
        The number of columns in the grid.
    cell_size : int
        The size of each cell in the grid.
    is_running : bool
        A flag indicating whether the game is running.
    generation : int
        The current generation count.
    canvas : tkinter.Canvas
        The canvas on which the grid is drawn.
    grid : list
        The current state of the grid.
    temp_grid : list
        A temporary grid used for updates."""
    def __init__(self, frame, app, rows=20, cols=20, cell_size=20):
        self.frame = frame
        self.app = app
        self.rows = rows
        self.cols = cols
        self.cell_size = cell_size
        self.is_running = False
        self.generation = 0
        pygame.mixer.init()
        pygame.mixer.music.set_volume(1.0)

        self.canvas = Canvas(frame, width=cols * cell_size, height=rows * cell_size, bg='white', highlightbackground="#ccc")
        self.canvas.pack(pady=20)

        self.grid = [[random.choice([0, 1]) for _ in range(cols)] for _ in range(rows)]
        self.temp_grid = [[0 for _ in range(cols)] for _ in range(rows)]

        self.alive_cells = sum(sum(row) for row in self.grid)
        self.is_drawing = False
        self.last_toggled_cell = None
        self.canvas.bind("<ButtonPress-1>", self.start_drawing)
        self.canvas.bind("<B1-Motion>", self.draw_cells)
        self.canvas.bind("<ButtonRelease-1>", self.stop_drawing)

        self.slider_frame = ctk.CTkFrame(frame)
        self.slider_frame.pack(pady=10)

        self.speed_scale = ctk.CTkSlider(self.slider_frame, from_=10, to=500, number_of_steps=49, command=self.update_speed)
        self.speed_scale.set(250)
        self.speed_scale.pack(side='left', padx=5)
        self.speed_label = ctk.CTkLabel(self.slider_frame, text="Speed: 250ms")
        self.speed_label.pack(side='left', padx=5)

        self.zoom_scale = ctk.CTkSlider(self.slider_frame, from_=10, to=37, number_of_steps=27, command=self.zoom_grid)
        self.zoom_scale.set(self.cell_size)
        self.zoom_scale.pack(side='left', padx=5)
        self.zoom_label = ctk.CTkLabel(self.slider_frame, text=f"Zoom: {self.cell_size}")
        self.zoom_label.pack(side='left', padx=5)

        self.color_frame = ctk.CTkFrame(frame)
        self.color_frame.pack(pady=10)

        self.info_var = ctk.StringVar(value="Generation: 0 | Alive Cells: 0")
        self.info_label = ctk.CTkLabel(frame, textvariable=self.info_var, font=("Arial", 14))
        self.info_label.pack(pady=10)

        self.alive_color = 'black'
        self.dead_color = 'white'

        self.alive_color_button = ctk.CTkButton(self.color_frame, text="Alive Color", command=lambda: [self.choose_alive_color(), play_sound_in_thread("sound_effects/click2.wav")],
                                                fg_color="#4CAF50", hover_color="#388E3C")
        self.alive_color_button.grid(row=0, column=0, padx=5)

        self.dead_color_button = ctk.CTkButton(self.color_frame, text="Dead Color", command=lambda: [self.choose_dead_color(), play_sound_in_thread("sound_effects/click2.wav")],
                                               fg_color="#757575", hover_color="#616161")
        self.dead_color_button.grid(row=0, column=1, padx=5)

        self.boundary_condition = 'Finite'
        self.boundary_conditions = ['Finite', 'Reflective', 'Toroidal', 'Infinite']
        self.boundary_combobox = ctk.CTkOptionMenu(self.color_frame, values=self.boundary_conditions, command=self.update_boundary_condition)
        self.boundary_combobox.set("Select Boundary")
        self.boundary_combobox.grid(row=1, column=0, padx=5)

        self.toggle_button = ctk.CTkButton(self.color_frame, text="Start", command=self.toggle_game,
                                           fg_color="#388E3C", hover_color="#2E7D32")
        self.toggle_button.grid(row=0, column=2, padx=5)

        self.clear_button = ctk.CTkButton(self.color_frame, text="Clear", command=lambda: [self.clear_grid(), play_sound_in_thread("sound_effects/reset.wav")],
                                          fg_color="#FF7043", hover_color="#F4511E")
        self.clear_button.grid(row=0, column=3, padx=5)

        self.randomize_button = ctk.CTkButton(self.color_frame, text="Randomize", command=lambda: [self.randomize_grid(), play_sound_in_thread("sound_effects/click2.wav")],
                                              fg_color="#FFCA28", hover_color="#FBC02D", text_color="#000000")
        self.randomize_button.grid(row=0, column=4, padx=5)

        self.lobby_button = ctk.CTkButton(self.color_frame, text="Lobby", command=self.return_to_lobby,
                                          fg_color="#607D8B", hover_color="#455A64")
        self.lobby_button.grid(row=0, column=5, padx=5)

        save_button = ctk.CTkButton(self.color_frame, text="Save Pattern", command=lambda: [self.save_pattern(), play_sound_in_thread("sound_effects/click2.wav")],
                                    fg_color="#1976D2", hover_color="#2196F3")
        save_button.grid(row=1, column=2, padx=5, pady=5)

        load_button = ctk.CTkButton(self.color_frame, text="Load Pattern", command=lambda: [self.load_pattern(), play_sound_in_thread("sound_effects/click2.wav")],
                                    fg_color="#607D8B", hover_color="#455A64")
        load_button.grid(row=1, column=3, padx=5, pady=5)

        self.draw_grid()
        self.update_canvas()
        self.update_info_display()


    def return_to_lobby(self):
        if hasattr(self.app, 'switch_frames') and hasattr(self.app, 'lobby'):
            self.app.switch_frames(self.app.lobby)
            play_sound_in_thread("sound_effects/navigate.wav")
        else:
            print("Error: Unable to return to lobby. Required attributes not found.")

    def toggle_cell(self, event):
        """
        Toggles the state of a cell in the grid based on a mouse click event.
        """
        x, y = event.x, event.y
        row = y // self.cell_size
        col = x // self.cell_size
        if 0 <= row < self.rows and 0 <= col < self.cols:
            current_cell = (row, col)
            if current_cell != self.last_toggled_cell:
                self.grid[row][col] = 1 if self.grid[row][col] == 0 else 0
                self.alive_cells += 1 if self.grid[row][col] == 1 else -1
                play_sound_in_thread("sound_effects/click_cell.wav")
                self.update_info_display()
                self.update_canvas()
                self.last_toggled_cell = current_cell

    def start_drawing(self, event):
        """
        Activates drawing mode on mouse press, toggling the cell state.

        Parameters:
        event (tkinter.Event): Mouse event with cursor position.
        """
        self.is_drawing = True
        self.toggle_cell(event)  

    def draw_cells(self, event):
        """Toggle cell state if drawing is active."""
        if self.is_drawing:
            self.toggle_cell(event)

    def stop_drawing(self, event):
        """End drawing mode."""
        self.is_drawing = False

    def draw_grid(self):
        for i in range(self.rows):
            for j in range(self.cols):
                color = self.alive_color if self.grid[i][j] == 1 else self.dead_color
                self.canvas.create_rectangle(j * self.cell_size, i * self.cell_size,
                                              (j + 1) * self.cell_size, (i + 1) * self.cell_size,
                                              fill=color, outline="#ccc")

    def place_pattern(self, x, y, pattern):
        start_row = y // self.cell_size
        start_col = x // self.cell_size
        for i, row in enumerate(pattern):
            for j, cell in enumerate(row):
                grid_row = start_row + i
                grid_col = start_col + j
                if 0 <= grid_row < self.rows and 0 <= grid_col < self.cols:
                    if self.grid[grid_row][grid_col] == 0 and cell == 1:
                        self.alive_cells += 1
                    elif self.grid[grid_row][grid_col] == 1 and cell == 0:
                        self.alive_cells -= 1
                    self.grid[grid_row][grid_col] = cell
        self.update_canvas()
        self.update_info_display()


    def update_canvas(self):
        self.canvas.delete("all")
        self.draw_grid()

    def update_boundary_condition(self, choice):
        self.boundary_condition = choice

    def update_grid(self, rows, cols):
        self.rows = rows
        self.cols = cols
        self.cell_size = int(self.zoom_scale.get())
        self.grid = [[random.choice([0, 1]) for _ in range(cols)] for _ in range(rows)]
        self.temp_grid = [[0 for _ in range(cols)] for _ in range(rows)]
        self.canvas.config(width=self.cols * self.cell_size, height=self.rows * self.cell_size)
        
        self.generation = 0
        self.alive_cells = sum(sum(row) for row in self.grid)
        
        self.update_info_display()
        self.update_canvas()

    def zoom_grid(self, value):
        self.cell_size = int(float(value))
        self.canvas.config(width=self.cols * self.cell_size, height=self.rows * self.cell_size)
        self.update_canvas()
        self.zoom_label.configure(text=f"Zoom: {self.cell_size}")

    def update_speed(self, value):
        speed = int(float(value))
        self.speed_label.configure(text=f"Speed: {speed}ms")

    def choose_alive_color(self):
        color = colorchooser.askcolor(title="Choose color for alive cells")[1]
        if color:
            self.alive_color = color
            self.update_canvas()

    def choose_dead_color(self):
        color = colorchooser.askcolor(title="Choose color for dead cells")[1]
        if color:
            self.dead_color = color
            self.update_canvas()

    def toggle_game(self):
        if self.is_running:
            self.stop_game()
            self.toggle_button.configure(text="Start")
            self.toggle_button.configure(fg_color="#388E3C", hover_color="#2E7D32")
            play_sound_in_thread("sound_effects/exit3.wav")
        else:
            self.start_game()
            self.toggle_button.configure(text="Pause")
            self.toggle_button.configure(fg_color="#FF7043", hover_color="#F4511E")
            play_sound_in_thread("sound_effects/click2.wav")

    def start_game(self):
        self.is_running = True
        self.run_game()

    def run_game(self):
        if self.is_running:
            self.update_cells()
            self.update_canvas()
            self.frame.after(int(self.speed_scale.get()), self.run_game)

    def stop_game(self):
        self.is_running = False

    def clear_grid(self):
        self.grid = [[0 for _ in range(self.cols)] for _ in range(self.rows)]
        self.generation = 0
        self.alive_cells = 0
        self.update_info_display()
        self.update_canvas()

    def randomize_grid(self):
        self.grid = [[random.choice([0, 1]) for _ in range(self.cols)] for _ in range(self.rows)]
        self.generation = 0
        self.alive_cells = sum(sum(row) for row in self.grid)
        self.update_info_display()
        self.update_canvas()

    def update_cells(self):
        self.generation += 1
        self.alive_cells = 0
        for i in range(self.rows):
            for j in range(self.cols):
                live_neighbors = self.count_live_neighbors(i, j)
                if self.grid[i][j] == 1:
                    self.temp_grid[i][j] = 1 if live_neighbors in (2, 3) else 0
                else:
                    self.temp_grid[i][j] = 1 if live_neighbors == 3 else 0
                self.alive_cells += self.temp_grid[i][j]
        self.grid, self.temp_grid = self.temp_grid, self.grid
        self.update_info_display()

    def update_info_display(self):
        self.info_var.set(f"Generation: {self.generation} | Alive Cells: {self.alive_cells}")

    def count_live_neighbors(self, row, col):
        def finite_boundary(i, j):
            return 0 <= i < self.rows and 0 <= j < self.cols
        def infinite_boundary(i, j):
                return self.grid[i][j] if (0 <= i < self.rows and 0 <= j < self.cols) else 0
        def reflective_boundary(i, j):
            reflected_i = max(0, min(i, self.rows - 1))
            reflected_j = max(0, min(j, self.cols - 1))
            return reflected_i, reflected_j

        def toroidal_boundary(i, j):
            ni = (i + self.rows) % self.rows
            nj = (j + self.cols) % self.cols
            return ni, nj

        count = 0
        for i in range(row - 1, row + 2):
            for j in range(col - 1, col + 2):
                if i == row and j == col:
                    continue

                if self.boundary_condition == 'Finite':
                    if finite_boundary(i, j):
                        count += self.grid[i][j]

                elif self.boundary_condition == 'Reflective':
                    reflected_i, reflected_j = reflective_boundary(i, j)
                    count += self.grid[reflected_i][reflected_j]

                elif self.boundary_condition == 'Toroidal':
                    ni, nj = toroidal_boundary(i, j)
                    count += self.grid[ni][nj]

                elif self.boundary_condition == 'Infinite':
                    count += infinite_boundary(i, j)

        return count

    def save_pattern(self):
        file_path = ctk.filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON files", "*.json")])
        if file_path:
            with open(file_path, "w") as file:
                json.dump(self.grid, file)

    def load_pattern(self):
        file_path = ctk.filedialog.askopenfilename(filetypes=[("JSON files", "*.json")])
        if file_path:
            with open(file_path, "r") as file:
                loaded_grid = json.load(file)
            
            loaded_rows = len(loaded_grid)
            loaded_cols = len(loaded_grid[0])
            
            if loaded_rows != self.rows or loaded_cols != self.cols:
                error_message = f"Grid size mismatch!\nCurrent grid: {self.rows}x{self.cols}\nLoaded pattern: {loaded_rows}x{loaded_cols}"
                messagebox.showerror("Error", error_message)
                return
            
            self.grid = loaded_grid
            self.alive_cells = sum(sum(row) for row in self.grid)
            self.generation = 0
            self.update_info_display()
            self.update_canvas()
