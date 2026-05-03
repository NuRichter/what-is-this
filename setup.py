#!/usr/bin/env python3
"""
Offensive Security AI Assistant - Automated Setup
==================================================
Author: NuRichter
Date: May 2026
Description: One-command installer untuk complete setup

LEGAL NOTICE:
This tool is for authorized security testing only.
Unauthorized use is illegal and punishable by law.
"""

import os
import sys
import subprocess
import platform
import json
import shutil
from pathlib import Path
from typing import List, Dict, Optional
import argparse

# Rich for beautiful terminal output
try:
    from rich.console import Console
    from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
    from rich.panel import Panel
    from rich.table import Table
    from rich import print as rprint
except ImportError:
    print("Installing rich library...")
    subprocess.run([sys.executable, "-m", "pip", "install", "rich"], check=True)
    from rich.console import Console
    from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
    from rich.panel import Panel
    from rich.table import Table
    from rich import print as rprint

console = Console()


class OffSecAISetup:
    """Main setup class untuk Offensive Security AI Assistant"""
    
    def __init__(self, auto_install: bool = False):
        self.auto_install = auto_install
        self.platform = platform.system()
        self.home_dir = Path.home()
        self.tools_dir = Path("C:/Tools/offsec-ai") if self.platform == "Windows" else Path.home() / "offsec-ai"
        
        # Configuration
        self.config = {
            "ollama_models": [
                "xploiter/the-xploiter",
                "qwen2.5-coder:14b",
                "qwen2.5-coder:1.5b",
            ],
            "optional_models": [
                "loading_ctf/elona",
                "xploiter/pentester",
            ],
            "python_packages": [
                "aider-chat",
                "ollama",
                "rich",
                "pyyaml",
                "requests",
                "gitpython",
            ]
        }
    
    def print_banner(self):
        """Display welcome banner"""
        banner = """
        ╔═══════════════════════════════════════════════════════════════╗
        ║                                                               ║
        ║   🔐 OFFENSIVE SECURITY AI ASSISTANT SETUP 🔐                ║
        ║                                                               ║
        ║   Automated installer for complete AI coding environment     ║
        ║   Optimized for: MSI Vector 16 HX RTX 5070 Ti               ║
        ║                                                               ║
        ║   ⚠️  FOR AUTHORIZED SECURITY TESTING ONLY  ⚠️              ║
        ║                                                               ║
        ╚═══════════════════════════════════════════════════════════════╝
        """
        console.print(banner, style="bold cyan")
    
    def print_legal_disclaimer(self):
        """Display legal disclaimer"""
        disclaimer = Panel(
            """[bold red]LEGAL DISCLAIMER[/bold red]

This tool is designed for [green]authorized security testing[/green] only.

✅ LEGAL USES:
  • Authorized penetration testing
  • Security research with permission
  • CTF competitions and learning labs
  • Academic/educational purposes

❌ ILLEGAL USES:
  • Unauthorized system access
  • Malicious hacking
  • Data theft or manipulation
  • Any illegal cyber activities

[yellow]By proceeding, you agree to use this tool only for legal purposes.
The author is NOT responsible for misuse.[/yellow]
            """,
            title="⚠️  IMPORTANT ⚠️",
            border_style="red"
        )
        console.print(disclaimer)
        
        if not self.auto_install:
            response = console.input("\n[bold]Do you agree? (yes/no): [/bold]")
            if response.lower() not in ["yes", "y"]:
                console.print("[red]Setup cancelled.[/red]")
                sys.exit(0)
    
    def check_system_requirements(self) -> bool:
        """Check if system meets requirements"""
        console.print("\n[bold cyan]Checking system requirements...[/bold cyan]")
        
        requirements = {
            "OS": "✅" if self.platform in ["Windows", "Linux", "Darwin"] else "❌",
            "Python": "❌",
            "RAM": "❌",
            "Storage": "❌",
        }
        
        # Check Python version
        python_version = sys.version_info
        if python_version.major == 3 and python_version.minor >= 12:
            requirements["Python"] = "✅"
        
        # Check RAM (simplified)
        try:
            if self.platform == "Windows":
                import wmi
                w = wmi.WMI()
                total_ram = sum([int(mem.Capacity) for mem in w.Win32_PhysicalMemory()]) / (1024**3)
                if total_ram >= 16:
                    requirements["RAM"] = "✅"
            else:
                requirements["RAM"] = "⚠️ (Manual check required)"
        except:
            requirements["RAM"] = "⚠️ (Could not detect)"
        
        # Check storage
        if shutil.disk_usage("/").free > 50 * (1024**3):  # 50GB
            requirements["Storage"] = "✅"
        
        # Display results
        table = Table(title="System Requirements Check")
        table.add_column("Requirement", style="cyan")
        table.add_column("Status", style="white")
        table.add_column("Details", style="dim")
        
        table.add_row("Operating System", requirements["OS"], self.platform)
        table.add_row("Python Version", requirements["Python"], f"{python_version.major}.{python_version.minor}.{python_version.micro}")
        table.add_row("RAM (16GB min)", requirements["RAM"], "Check manually if needed")
        table.add_row("Storage (50GB min)", requirements["Storage"], "For models and projects")
        
        console.print(table)
        
        all_met = all(status in ["✅", "⚠️"] for status in requirements.values())
        return all_met
    
    def install_ollama(self) -> bool:
        """Install Ollama"""
        console.print("\n[bold cyan]Installing Ollama...[/bold cyan]")
        
        try:
            # Check if Ollama already installed
            result = subprocess.run(["ollama", "--version"], capture_output=True, text=True)
            if result.returncode == 0:
                console.print("[green]✓ Ollama already installed[/green]")
                console.print(f"  Version: {result.stdout.strip()}")
                return True
        except FileNotFoundError:
            pass
        
        # Install based on platform
        if self.platform == "Windows":
            console.print("[yellow]Please install Ollama manually:[/yellow]")
            console.print("  1. Run: [cyan]winget install Ollama.Ollama[/cyan]")
            console.print("  2. Or download from: [cyan]https://ollama.com/download/windows[/cyan]")
            
            if not self.auto_install:
                input("\nPress Enter after installing Ollama...")
                return self.verify_ollama_installation()
            return False
        
        elif self.platform == "Linux":
            console.print("Installing Ollama for Linux...")
            subprocess.run(["curl", "-fsSL", "https://ollama.com/install.sh"], stdout=subprocess.PIPE)
            return True
        
        elif self.platform == "Darwin":
            console.print("Installing Ollama for macOS...")
            subprocess.run(["brew", "install", "ollama"], check=True)
            return True
        
        return False
    
    def verify_ollama_installation(self) -> bool:
        """Verify Ollama is properly installed and running"""
        try:
            # Check version
            result = subprocess.run(["ollama", "--version"], capture_output=True, text=True)
            if result.returncode != 0:
                return False
            
            # Check if service is running
            import requests
            response = requests.get("http://localhost:11434", timeout=5)
            if response.status_code == 200:
                console.print("[green]✓ Ollama is running[/green]")
                return True
            else:
                console.print("[yellow]⚠ Ollama installed but not running[/yellow]")
                console.print("  Starting Ollama service...")
                # Try to start service
                if self.platform == "Windows":
                    subprocess.Popen(["ollama", "serve"], creationflags=subprocess.CREATE_NEW_CONSOLE)
                else:
                    subprocess.Popen(["ollama", "serve"])
                
                import time
                time.sleep(3)
                return True
        except Exception as e:
            console.print(f"[red]✗ Error verifying Ollama: {e}[/red]")
            return False
    
    def configure_ollama(self):
        """Configure Ollama environment variables"""
        console.print("\n[bold cyan]Configuring Ollama...[/bold cyan]")
        
        env_vars = {
            "OLLAMA_CONTEXT_LENGTH": "32768",
            "OLLAMA_NUM_PARALLEL": "4",
        }
        
        if self.platform == "Windows":
            for key, value in env_vars.items():
                console.print(f"  Setting {key}={value}")
                subprocess.run(["setx", key, value], check=True)
            console.print("[green]✓ Environment variables set (restart shell required)[/green]")
        else:
            shell_rc = self.home_dir / ".bashrc"
            with open(shell_rc, "a") as f:
                f.write("\n# Ollama configuration\n")
                for key, value in env_vars.items():
                    f.write(f"export {key}={value}\n")
            console.print(f"[green]✓ Added to {shell_rc}[/green]")
    
    def pull_models(self):
        """Pull required Ollama models"""
        console.print("\n[bold cyan]Downloading AI models...[/bold cyan]")
        console.print("[yellow]This may take 20-30 minutes depending on your connection[/yellow]\n")
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            console=console
        ) as progress:
            
            # Pull main models
            for model in self.config["ollama_models"]:
                task = progress.add_task(f"Pulling {model}...", total=None)
                try:
                    result = subprocess.run(
                        ["ollama", "pull", model],
                        capture_output=True,
                        text=True,
                        timeout=1800  # 30 minutes timeout
                    )
                    if result.returncode == 0:
                        progress.update(task, description=f"[green]✓ {model}[/green]")
                        console.print(f"  [green]Successfully pulled {model}[/green]")
                    else:
                        progress.update(task, description=f"[red]✗ {model}[/red]")
                        console.print(f"  [red]Failed to pull {model}: {result.stderr}[/red]")
                except subprocess.TimeoutExpired:
                    progress.update(task, description=f"[red]✗ {model} (timeout)[/red]")
                    console.print(f"  [red]Timeout pulling {model}[/red]")
                except Exception as e:
                    progress.update(task, description=f"[red]✗ {model}[/red]")
                    console.print(f"  [red]Error pulling {model}: {e}[/red]")
            
            # Ask about optional models
            if not self.auto_install:
                console.print("\n[bold]Optional models available:[/bold]")
                for model in self.config["optional_models"]:
                    console.print(f"  • {model}")
                
                response = console.input("\nPull optional models? (yes/no): ")
                if response.lower() in ["yes", "y"]:
                    for model in self.config["optional_models"]:
                        task = progress.add_task(f"Pulling {model}...", total=None)
                        subprocess.run(["ollama", "pull", model])
                        progress.update(task, description=f"[green]✓ {model}[/green]")
    
    def install_python_packages(self):
        """Install required Python packages"""
        console.print("\n[bold cyan]Installing Python packages...[/bold cyan]")
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            
            for package in self.config["python_packages"]:
                task = progress.add_task(f"Installing {package}...", total=None)
                try:
                    subprocess.run(
                        [sys.executable, "-m", "pip", "install", package, "--quiet"],
                        check=True,
                        capture_output=True
                    )
                    progress.update(task, description=f"[green]✓ {package}[/green]")
                except subprocess.CalledProcessError as e:
                    progress.update(task, description=f"[red]✗ {package}[/red]")
                    console.print(f"  [red]Failed to install {package}[/red]")
        
        console.print("[green]✓ Python packages installed[/green]")
    
    def create_aider_config(self):
        """Create Aider configuration file"""
        console.print("\n[bold cyan]Creating Aider configuration...[/bold cyan]")
        
        config_content = """# Aider configuration for Offensive Security
# Model configuration
model: ollama_chat/xploiter/the-xploiter
editor-model: ollama_chat/qwen2.5-coder:14b

# Ollama settings
ollama-api-base: http://localhost:11434

# Context settings
num-ctx: 32768

# Auto-commit settings
auto-commits: true
dirty-commits: true

# Review changes before applying
yes: false

# Additional settings
dark-mode: true
pretty: true
show-diffs: true

# Git settings
git: true
gitignore: true

# Output settings
stream: true
"""
        
        config_path = self.home_dir / ".aider.conf.yml"
        with open(config_path, "w") as f:
            f.write(config_content)
        
        console.print(f"[green]✓ Created {config_path}[/green]")
    
    def create_directory_structure(self):
        """Create project directory structure"""
        console.print("\n[bold cyan]Creating directory structure...[/bold cyan]")
        
        directories = [
            self.tools_dir,
            self.tools_dir / "projects",
            self.tools_dir / "scripts",
            self.tools_dir / "templates",
            self.tools_dir / "logs",
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
            console.print(f"  [green]✓ {directory}[/green]")
    
    def run_verification(self):
        """Run verification tests"""
        console.print("\n[bold cyan]Running verification tests...[/bold cyan]")
        
        tests = {
            "Ollama service": False,
            "Models available": False,
            "Aider installed": False,
            "Python packages": False,
        }
        
        # Test Ollama
        try:
            import requests
            response = requests.get("http://localhost:11434", timeout=5)
            tests["Ollama service"] = response.status_code == 200
        except:
            pass
        
        # Test models
        try:
            result = subprocess.run(["ollama", "list"], capture_output=True, text=True)
            tests["Models available"] = "xploiter/the-xploiter" in result.stdout
        except:
            pass
        
        # Test Aider
        try:
            result = subprocess.run(["aider", "--version"], capture_output=True, text=True)
            tests["Aider installed"] = result.returncode == 0
        except:
            pass
        
        # Test Python packages
        try:
            import aider
            import ollama
            tests["Python packages"] = True
        except:
            pass
        
        # Display results
        table = Table(title="Verification Results")
        table.add_column("Test", style="cyan")
        table.add_column("Status", style="white")
        
        for test, passed in tests.items():
            status = "[green]✓ PASS[/green]" if passed else "[red]✗ FAIL[/red]"
            table.add_row(test, status)
        
        console.print(table)
        
        all_passed = all(tests.values())
        return all_passed
    
    def print_next_steps(self):
        """Print next steps after installation"""
        next_steps = Panel(
            """[bold green]Setup Complete! 🎉[/bold green]

[bold cyan]Next Steps:[/bold cyan]

1. [yellow]Restart your terminal/PowerShell[/yellow] to load environment variables

2. [yellow]Test the installation:[/yellow]
   [cyan]python test_model.py[/cyan]

3. [yellow]Generate your first project:[/yellow]
   [cyan]python generate_pentest_project.py --type web-scanner[/cyan]

4. [yellow]Start Aider for interactive coding:[/yellow]
   [cyan]aider --model ollama_chat/xploiter/the-xploiter[/cyan]

5. [yellow]Read the documentation:[/yellow]
   [cyan]Open README.md for detailed usage guide[/cyan]

[bold red]REMEMBER:[/bold red] Use these tools responsibly and legally!

[bold]Quick Commands:[/bold]
• [cyan]ollama list[/cyan] - View installed models
• [cyan]aider --help[/cyan] - Aider help
• [cyan]python verify_setup.py[/cyan] - Re-run verification

[bold green]Happy Ethical Hacking! 🔐[/bold green]
            """,
            title="✨ Installation Complete ✨",
            border_style="green"
        )
        console.print(next_steps)
    
    def run(self):
        """Main setup runner"""
        try:
            self.print_banner()
            self.print_legal_disclaimer()
            
            if not self.check_system_requirements():
                console.print("\n[red]System requirements not met![/red]")
                sys.exit(1)
            
            # Installation steps
            steps = [
                ("Installing Ollama", self.install_ollama),
                ("Configuring Ollama", self.configure_ollama),
                ("Pulling AI models", self.pull_models),
                ("Installing Python packages", self.install_python_packages),
                ("Creating Aider config", self.create_aider_config),
                ("Creating directories", self.create_directory_structure),
            ]
            
            for step_name, step_func in steps:
                console.print(f"\n[bold]→ {step_name}...[/bold]")
                step_func()
            
            # Verification
            console.print("\n" + "="*60)
            verification_passed = self.run_verification()
            console.print("="*60)
            
            if verification_passed:
                self.print_next_steps()
            else:
                console.print("\n[yellow]⚠ Some verification tests failed[/yellow]")
                console.print("Please check the errors above and retry.")
            
        except KeyboardInterrupt:
            console.print("\n[yellow]Setup interrupted by user[/yellow]")
            sys.exit(1)
        except Exception as e:
            console.print(f"\n[red]Setup failed: {e}[/red]")
            import traceback
            console.print(traceback.format_exc())
            sys.exit(1)


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Offensive Security AI Assistant - Automated Setup"
    )
    parser.add_argument(
        "--auto-install",
        action="store_true",
        help="Run installation without prompts (use with caution)"
    )
    
    args = parser.parse_args()
    
    setup = OffSecAISetup(auto_install=args.auto_install)
    setup.run()


if __name__ == "__main__":
    main()
