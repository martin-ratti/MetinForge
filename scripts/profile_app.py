import cProfile
import pstats
import sys
import os
from PyQt6.QtWidgets import QApplication

# Add app to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from app.main import MainWindow

def profile_startup():
    """Profile the application startup process."""
    app = QApplication(sys.argv)
    
    profiler = cProfile.Profile()
    profiler.enable()
    
    # Init main window (this triggers controllers, DB, views)
    window = MainWindow()
    window.show()
    
    profiler.disable()
    
    # Process immediately without running the event loop for too long
    # We just want to measure initialization cost
    
    stats = pstats.Stats(profiler)
    stats.sort_stats(pstats.SortKey.CUMULATIVE)
    stats.print_stats(20)
    stats.dump_stats("startup_profile.prof")
    print("Profile saved to startup_profile.prof")

if __name__ == "__main__":
    profile_startup()
