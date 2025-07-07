from models.registro import Base
from services.db import engine
from ui import main_tkinter

if __name__ == "__main__":
    Base.metadata.create_all(bind=engine)
    # main_tkinter.main() # Esto lanza la interfaz gráfica