"""
AutoClicker GUI - Aplicación gráfica para clicks automáticos
Mantén presionada una tecla para hacer clicks automáticos en la posición del cursor.
"""
import tkinter as tk
from tkinter import ttk, messagebox
import threading
import time
from pynput import mouse, keyboard
from pynput.keyboard import Key, KeyCode


class AutoClickerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("PUTAMADRE V1")
        self.root.geometry("500x600")
        self.root.resizable(False, False)

        # Configurar estilo
        self.setup_styles()

        # Controladores
        self.mouse_controller = mouse.Controller()
        self.keyboard_listener = None

        # Estado
        self.clicking_left = False
        self.clicking_right = False
        self.is_running = False

        # Configuración por defecto (autocompletada)
        self.left_click_key = KeyCode.from_char('z')
        self.right_click_key = KeyCode.from_char('x')
        self.click_speed = 10
        self.click_delay = 1.0 / self.click_speed

        # Threads
        self.left_thread = None
        self.right_thread = None

        # Variables de configuración
        self.waiting_for_key = None

        # Crear interfaz
        self.create_widgets()

        # Protocolo de cierre
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    def setup_styles(self):
        """Configura los estilos de la interfaz"""
        style = ttk.Style()
        style.theme_use('clam')

        # Colores
        bg_color = "#2b2b2b"
        fg_color = "#ffffff"
        accent_color = "#4a9eff"

        self.root.configure(bg=bg_color)

    def create_widgets(self):
        """Crea todos los widgets de la interfaz"""

        # Frame principal
        main_frame = tk.Frame(self.root, bg="#2b2b2b", padx=20, pady=20)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Título
        title_label = tk.Label(
            main_frame,
            text="PUTAMADRE V1",
            font=("Arial", 24, "bold"),
            bg="#2b2b2b",
            fg="#4a9eff"
        )
        title_label.pack(pady=(0, 20))

        # Frame de configuración de teclas
        keys_frame = tk.LabelFrame(
            main_frame,
            text="Configuración de Teclas",
            font=("Arial", 12, "bold"),
            bg="#363636",
            fg="#ffffff",
            padx=15,
            pady=15
        )
        keys_frame.pack(fill=tk.X, pady=(0, 15))

        # Click Izquierdo
        left_frame = tk.Frame(keys_frame, bg="#363636")
        left_frame.pack(fill=tk.X, pady=5)

        tk.Label(
            left_frame,
            text="Click Izquierdo:",
            font=("Arial", 11),
            bg="#363636",
            fg="#ffffff",
            width=15,
            anchor="w"
        ).pack(side=tk.LEFT)

        self.left_key_label = tk.Label(
            left_frame,
            text=self.format_key(self.left_click_key),
            font=("Arial", 11, "bold"),
            bg="#4a9eff",
            fg="#ffffff",
            width=8,
            relief=tk.RAISED,
            padx=10,
            pady=5
        )
        self.left_key_label.pack(side=tk.LEFT, padx=10)

        tk.Button(
            left_frame,
            text="Cambiar",
            command=lambda: self.configure_key('left'),
            bg="#555555",
            fg="#ffffff",
            font=("Arial", 10),
            relief=tk.FLAT,
            cursor="hand2",
            padx=15,
            pady=5
        ).pack(side=tk.LEFT)

        # Click Derecho
        right_frame = tk.Frame(keys_frame, bg="#363636")
        right_frame.pack(fill=tk.X, pady=5)

        tk.Label(
            right_frame,
            text="Click Derecho:",
            font=("Arial", 11),
            bg="#363636",
            fg="#ffffff",
            width=15,
            anchor="w"
        ).pack(side=tk.LEFT)

        self.right_key_label = tk.Label(
            right_frame,
            text=self.format_key(self.right_click_key),
            font=("Arial", 11, "bold"),
            bg="#ff6b6b",
            fg="#ffffff",
            width=8,
            relief=tk.RAISED,
            padx=10,
            pady=5
        )
        self.right_key_label.pack(side=tk.LEFT, padx=10)

        tk.Button(
            right_frame,
            text="Cambiar",
            command=lambda: self.configure_key('right'),
            bg="#555555",
            fg="#ffffff",
            font=("Arial", 10),
            relief=tk.FLAT,
            cursor="hand2",
            padx=15,
            pady=5
        ).pack(side=tk.LEFT)

        # Frame de velocidad
        speed_frame = tk.LabelFrame(
            main_frame,
            text="Velocidad de Clicks",
            font=("Arial", 12, "bold"),
            bg="#363636",
            fg="#ffffff",
            padx=15,
            pady=15
        )
        speed_frame.pack(fill=tk.X, pady=(0, 15))

        # Slider de velocidad
        speed_control_frame = tk.Frame(speed_frame, bg="#363636")
        speed_control_frame.pack(fill=tk.X)

        self.speed_var = tk.IntVar(value=self.click_speed)
        self.speed_label = tk.Label(
            speed_control_frame,
            text=f"{self.click_speed} clicks/seg",
            font=("Arial", 14, "bold"),
            bg="#363636",
            fg="#4a9eff"
        )
        self.speed_label.pack(pady=(0, 10))

        speed_slider = tk.Scale(
            speed_control_frame,
            from_=1,
            to=50,
            orient=tk.HORIZONTAL,
            variable=self.speed_var,
            command=self.update_speed,
            bg="#555555",
            fg="#ffffff",
            highlightthickness=0,
            troughcolor="#2b2b2b",
            activebackground="#4a9eff",
            length=300
        )
        speed_slider.pack()

        # Frame de estado
        status_frame = tk.LabelFrame(
            main_frame,
            text="Estado",
            font=("Arial", 12, "bold"),
            bg="#363636",
            fg="#ffffff",
            padx=15,
            pady=15
        )
        status_frame.pack(fill=tk.X, pady=(0, 15))

        # Indicadores de estado
        indicators_frame = tk.Frame(status_frame, bg="#363636")
        indicators_frame.pack()

        # Indicador izquierdo
        left_ind_frame = tk.Frame(indicators_frame, bg="#363636")
        left_ind_frame.pack(side=tk.LEFT, padx=20)

        self.left_indicator = tk.Canvas(left_ind_frame, width=20, height=20, bg="#363636", highlightthickness=0)
        self.left_indicator.pack()
        self.left_indicator_circle = self.left_indicator.create_oval(2, 2, 18, 18, fill="#555555", outline="")

        tk.Label(
            left_ind_frame,
            text="Click Izq.",
            font=("Arial", 9),
            bg="#363636",
            fg="#ffffff"
        ).pack()

        # Indicador derecho
        right_ind_frame = tk.Frame(indicators_frame, bg="#363636")
        right_ind_frame.pack(side=tk.LEFT, padx=20)

        self.right_indicator = tk.Canvas(right_ind_frame, width=20, height=20, bg="#363636", highlightthickness=0)
        self.right_indicator.pack()
        self.right_indicator_circle = self.right_indicator.create_oval(2, 2, 18, 18, fill="#555555", outline="")

        tk.Label(
            right_ind_frame,
            text="Click Der.",
            font=("Arial", 9),
            bg="#363636",
            fg="#ffffff"
        ).pack()

        # Estado general
        self.status_text = tk.Label(
            status_frame,
            text="Detenido",
            font=("Arial", 12),
            bg="#363636",
            fg="#888888"
        )
        self.status_text.pack(pady=(10, 0))

        # Botón de inicio/parada
        self.toggle_button = tk.Button(
            main_frame,
            text="INICIAR",
            command=self.toggle_autoclicker,
            bg="#4CAF50",
            fg="#ffffff",
            font=("Arial", 14, "bold"),
            relief=tk.FLAT,
            cursor="hand2",
            padx=20,
            pady=15,
            activebackground="#45a049"
        )
        self.toggle_button.pack(fill=tk.X, pady=(0, 10))

        # Instrucciones
        instructions_frame = tk.Frame(main_frame, bg="#2b2b2b")
        instructions_frame.pack(fill=tk.X)

        tk.Label(
            instructions_frame,
            text="Instrucciones:",
            font=("Arial", 10, "bold"),
            bg="#2b2b2b",
            fg="#4a9eff",
            anchor="w"
        ).pack(fill=tk.X, pady=(0, 5))

        instructions = [
            "- Presiona INICIAR para activar el autoclicker",
            "- Manten presionada la tecla asignada para clickear",
            "- Suelta la tecla para detener los clicks",
            "- Presiona ESC para pausar/reanudar el autoclicker"
        ]

        for instruction in instructions:
            tk.Label(
                instructions_frame,
                text=instruction,
                font=("Arial", 9),
                bg="#2b2b2b",
                fg="#cccccc",
                anchor="w"
            ).pack(fill=tk.X)

    def format_key(self, key):
        """Formatea el nombre de una tecla para mostrar"""
        if isinstance(key, KeyCode):
            if key.char:
                return key.char.upper()
        elif isinstance(key, Key):
            return key.name.upper()
        return str(key)

    def configure_key(self, click_type):
        """Configura una tecla para un tipo de click"""
        if self.is_running:
            messagebox.showwarning("Advertencia", "Deten el autoclicker antes de cambiar las teclas")
            return

        self.waiting_for_key = click_type

        # Crear ventana de configuración
        config_window = tk.Toplevel(self.root)
        config_window.title("Configurar Tecla")
        config_window.geometry("300x150")
        config_window.resizable(False, False)
        config_window.configure(bg="#2b2b2b")
        config_window.transient(self.root)
        config_window.grab_set()

        # Centrar ventana
        config_window.geometry("+%d+%d" % (
            self.root.winfo_x() + 100,
            self.root.winfo_y() + 200
        ))

        tk.Label(
            config_window,
            text=f"Presiona la tecla para\n{'Click Izquierdo' if click_type == 'left' else 'Click Derecho'}",
            font=("Arial", 12),
            bg="#2b2b2b",
            fg="#ffffff"
        ).pack(pady=30)

        waiting_label = tk.Label(
            config_window,
            text="Esperando tecla...",
            font=("Arial", 10),
            bg="#2b2b2b",
            fg="#4a9eff"
        )
        waiting_label.pack()

        def on_key_press(key):
            if click_type == 'left':
                self.left_click_key = key
                self.left_key_label.config(text=self.format_key(key))
            else:
                self.right_click_key = key
                self.right_key_label.config(text=self.format_key(key))

            self.waiting_for_key = None
            config_window.destroy()
            return False

        # Listener temporal
        temp_listener = keyboard.Listener(on_press=on_key_press)
        temp_listener.start()

        def on_close():
            temp_listener.stop()
            self.waiting_for_key = None
            config_window.destroy()

        config_window.protocol("WM_DELETE_WINDOW", on_close)

    def update_speed(self, value):
        """Actualiza la velocidad de clicks"""
        self.click_speed = int(value)
        self.click_delay = 1.0 / self.click_speed
        self.speed_label.config(text=f"{self.click_speed} clicks/seg")

    def click_loop_left(self):
        """Loop de clicks izquierdos"""
        while self.clicking_left and self.is_running:
            self.mouse_controller.click(mouse.Button.left, 1)
            time.sleep(self.click_delay)

    def click_loop_right(self):
        """Loop de clicks derechos"""
        while self.clicking_right and self.is_running:
            self.mouse_controller.click(mouse.Button.right, 1)
            time.sleep(self.click_delay)

    def on_press(self, key):
        """Maneja eventos de tecla presionada"""
        if not self.is_running:
            return

        try:
            # Click izquierdo
            if key == self.left_click_key and not self.clicking_left:
                self.clicking_left = True
                self.left_thread = threading.Thread(target=self.click_loop_left, daemon=True)
                self.left_thread.start()
                self.root.after(0, lambda: self.left_indicator.itemconfig(
                    self.left_indicator_circle, fill="#4a9eff"
                ))

            # Click derecho
            elif key == self.right_click_key and not self.clicking_right:
                self.clicking_right = True
                self.right_thread = threading.Thread(target=self.click_loop_right, daemon=True)
                self.right_thread.start()
                self.root.after(0, lambda: self.right_indicator.itemconfig(
                    self.right_indicator_circle, fill="#ff6b6b"
                ))

        except AttributeError:
            pass

    def on_release(self, key):
        """Maneja eventos de tecla liberada"""
        if not self.is_running:
            return

        try:
            # Detener click izquierdo
            if key == self.left_click_key and self.clicking_left:
                self.clicking_left = False
                self.root.after(0, lambda: self.left_indicator.itemconfig(
                    self.left_indicator_circle, fill="#555555"
                ))

            # Detener click derecho
            elif key == self.right_click_key and self.clicking_right:
                self.clicking_right = False
                self.root.after(0, lambda: self.right_indicator.itemconfig(
                    self.right_indicator_circle, fill="#555555"
                ))

            # Pausar/reanudar con ESC
            if key == Key.esc:
                self.root.after(0, self.toggle_autoclicker)

        except AttributeError:
            pass

    def toggle_autoclicker(self):
        """Inicia o detiene el autoclicker"""
        if not self.is_running:
            # Iniciar
            self.is_running = True
            self.toggle_button.config(
                text="PAUSAR (o presiona ESC)",
                bg="#ff6b6b",
                activebackground="#e55555"
            )
            self.status_text.config(text="Activo - Listo para clickear", fg="#4CAF50")

            # Iniciar listener
            self.keyboard_listener = keyboard.Listener(
                on_press=self.on_press,
                on_release=self.on_release
            )
            self.keyboard_listener.start()
        else:
            # Detener
            self.is_running = False
            self.clicking_left = False
            self.clicking_right = False

            self.toggle_button.config(
                text="INICIAR",
                bg="#4CAF50",
                activebackground="#45a049"
            )
            self.status_text.config(text="Detenido", fg="#888888")

            # Resetear indicadores
            self.left_indicator.itemconfig(self.left_indicator_circle, fill="#555555")
            self.right_indicator.itemconfig(self.right_indicator_circle, fill="#555555")

            # Detener listener
            if self.keyboard_listener:
                self.keyboard_listener.stop()
                self.keyboard_listener = None

    def on_closing(self):
        """Maneja el cierre de la ventana"""
        if self.is_running:
            self.toggle_autoclicker()

        if self.keyboard_listener:
            self.keyboard_listener.stop()

        self.root.destroy()


def main():
    """Función principal"""
    root = tk.Tk()
    app = AutoClickerGUI(root)
    root.mainloop()


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        messagebox.showerror("Error", f"Ha ocurrido un error:\n{str(e)}")
