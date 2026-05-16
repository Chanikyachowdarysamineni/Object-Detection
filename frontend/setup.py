#!/usr/bin/env python3
"""
Quick Setup Script for Real-Time Object Detection App
Handles environment setup, dependency installation, and database initialization
"""

import os
import sys
import subprocess
import platform
from pathlib import Path


class Setup:
    def __init__(self):
        self.platform = platform.system()
        self.project_root = Path(__file__).parent
        self.is_windows = self.platform == 'Windows'
        self.is_mac = self.platform == 'Darwin'
        self.is_linux = self.platform == 'Linux'

    def print_header(self, text):
        """Print formatted header."""
        print("\n" + "=" * 60)
        print(f"  {text}")
        print("=" * 60 + "\n")

    def run_command(self, cmd, description=""):
        """Run shell command."""
        if description:
            print(f"▶️  {description}...")
        try:
            result = subprocess.run(
                cmd,
                shell=True,
                check=True,
                capture_output=False,
                cwd=str(self.project_root)
            )
            print("✅ Done\n")
            return True
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed: {str(e)}\n")
            return False

    def create_venv(self):
        """Create Python virtual environment."""
        self.print_header("Creating Virtual Environment")
        
        venv_path = self.project_root / "venv"
        if venv_path.exists():
            print(f"✅ Virtual environment already exists at {venv_path}\n")
            return str(venv_path)
        
        cmd = f"python -m venv venv"
        if self.run_command(cmd, "Creating virtual environment"):
            return str(venv_path)
        return None

    def get_pip_command(self):
        """Get pip command for current platform."""
        if self.is_windows:
            return "venv\\Scripts\\pip"
        else:
            return "venv/bin/pip"

    def install_dependencies(self):
        """Install Python dependencies."""
        self.print_header("Installing Dependencies")
        
        pip_cmd = self.get_pip_command()
        
        # Upgrade pip
        if not self.run_command(f"{pip_cmd} install --upgrade pip setuptools wheel", "Upgrading pip"):
            return False
        
        # Install requirements
        if not self.run_command(f"{pip_cmd} install -r requirements.txt", "Installing requirements"):
            return False
        
        return True

    def setup_env_file(self):
        """Setup .env file."""
        self.print_header("Setting Up Environment File")
        
        env_file = self.project_root / ".env"
        env_example = self.project_root / ".env.example"
        
        if env_file.exists():
            print(f"✅ .env file already exists\n")
            return True
        
        if env_example.exists():
            import shutil
            shutil.copy(env_example, env_file)
            print(f"✅ Created .env from .env.example")
            print(f"📝 Please edit {env_file} with your PostgreSQL credentials\n")
            return True
        
        print("❌ .env.example not found\n")
        return False

    def check_postgres(self):
        """Check PostgreSQL installation."""
        self.print_header("Checking PostgreSQL")
        
        try:
            result = subprocess.run(
                "psql --version",
                shell=True,
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                print(f"✅ PostgreSQL installed: {result.stdout.strip()}\n")
                return True
        except:
            pass
        
        print("⚠️  PostgreSQL not found in PATH")
        print("📖 Install from: https://www.postgresql.org/download/\n")
        return False

    def init_database(self):
        """Initialize database."""
        self.print_header("Initializing Database")
        
        python_cmd = "python" if self.is_windows else "python3"
        
        # Check if migrations script exists
        init_script = self.project_root / "backend" / "migrations" / "init_db.py"
        if not init_script.exists():
            print(f"❌ Database initialization script not found\n")
            return False
        
        if self.run_command(
            f"{python_cmd} backend/migrations/init_db.py",
            "Initializing database tables"
        ):
            print("✅ Database initialized successfully\n")
            return True
        
        return False

    def create_project_structure(self):
        """Ensure project directories exist."""
        self.print_header("Creating Project Directories")
        
        dirs = [
            "logs",
            "backend/app",
            "backend/app/routers",
            "backend/app/models",
            "backend/app/services",
            "backend/app/schemas",
            "backend/app/core",
            "frontend-gradio",
        ]
        
        for d in dirs:
            path = self.project_root / d
            path.mkdir(parents=True, exist_ok=True)
            print(f"✅ {d}/")
        
        print()

    def install_pytorch_gpu(self):
        """Install PyTorch with GPU support."""
        self.print_header("GPU Support (Optional)")
        
        print("PyTorch GPU support:")
        print("1. Automatic (skip - uses CPU)")
        print("2. NVIDIA CUDA 11.8")
        print("3. NVIDIA CUDA 12.1")
        print("4. M1/M2 Mac")
        print("5. CPU only\n")
        
        choice = input("Select option (1-5) [default: 1]: ").strip() or "1"
        
        pip_cmd = self.get_pip_command()
        
        if choice == "2":
            print("\n🔧 Installing PyTorch with CUDA 11.8...")
            self.run_command(
                f"{pip_cmd} install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118",
                "Installing PyTorch (CUDA 11.8)"
            )
        elif choice == "3":
            print("\n🔧 Installing PyTorch with CUDA 12.1...")
            self.run_command(
                f"{pip_cmd} install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121",
                "Installing PyTorch (CUDA 12.1)"
            )
        elif choice in ["4", "5"]:
            print("\n✅ PyTorch CPU version already included in requirements.txt")
        else:
            print("✅ Skipping GPU setup")
        
        print()

    def print_next_steps(self):
        """Print next steps."""
        self.print_header("Setup Complete! 🎉")
        
        print("📋 Next Steps:")
        print("-" * 60)
        print("\n1. ⚙️  Configure PostgreSQL")
        print("   - Ensure PostgreSQL is running")
        print("   - Edit .env with your database credentials")
        print("   - Run: python backend/migrations/init_db.py")
        
        print("\n2. 🚀 Start the Application")
        
        if self.is_windows:
            print("   - Windows: start.bat")
        else:
            print("   - Linux/Mac: bash start.sh")
        
        print("   - Or manually:")
        print("     Terminal 1: cd backend && python -m uvicorn app.main:app --reload")
        print("     Terminal 2: cd frontend-gradio && python app.py")
        
        print("\n3. 🌐 Access Application")
        print("   - Gradio UI: http://localhost:7860")
        print("   - API Docs: http://localhost:8000/docs")
        print("   - ReDoc: http://localhost:8000/redoc")
        
        print("\n4 📚 Documentation")
        print("   - API Endpoints: docs/API.md")
        print("   - Installation: docs/INSTALLATION.md")
        print("   - Training: docs/TRAINING.md")
        print("   - README: README.md")
        
        print("\n" + "=" * 60)
        print("  Happy coding! 🚀")
        print("=" * 60 + "\n")

    def run(self):
        """Run full setup."""
        print("\n")
        print("╔" + "=" * 58 + "╗")
        print("║  Real-Time Object Detection - Setup Wizard  ║")
        print("╚" + "=" * 58 + "╝")
        
        # Check platform
        print(f"\n🖥️  Detected Platform: {self.platform}")
        
        # Create project structure
        self.create_project_structure()
        
        # Create virtual environment
        venv = self.create_venv()
        if not venv:
            print("❌ Failed to create virtual environment")
            sys.exit(1)
        
        # Install dependencies
        if not self.install_dependencies():
            print("❌ Failed to install dependencies")
            sys.exit(1)
        
        # Setup PyTorch GPU (optional)
        self.install_pytorch_gpu()
        
        # Setup .env file
        if not self.setup_env_file():
            print("⚠️  Could not create .env file")
        
        # Check PostgreSQL
        has_postgres = self.check_postgres()
        
        # Initialize database
        if has_postgres:
            response = input("Initialize database now? (y/n) [default: y]: ").strip().lower() or "y"
            if response == "y":
                if not self.init_database():
                    print("⚠️  Database initialization failed. You can run it later:")
                    print("   python backend/migrations/init_db.py")
        else:
            print("⚠️  Skipping database initialization (PostgreSQL not found)")
            print("   Install PostgreSQL and run: python backend/migrations/init_db.py")
        
        # Print next steps
        self.print_next_steps()


if __name__ == "__main__":
    setup = Setup()
    setup.run()
