# 🔐 Offensive Cybersecurity AI Assistant Setup

> **Complete guide untuk setup AI coding assistant khusus Offensive Security di Windows 11**  
> **Updated: May 2026** | **Author: NuRichter** | **Hardware: MSI Vector 16 HX RTX 5070 Ti**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Ollama](https://img.shields.io/badge/Ollama-0.6+-blue.svg)](https://ollama.com/)
[![Python](https://img.shields.io/badge/Python-3.12-green.svg)](https://www.python.org/)

---

## ⚠️ LEGAL DISCLAIMER

```
┌─────────────────────────────────────────────────────────────┐
│  PENTING - BACA SEBELUM MELANJUTKAN                         │
├─────────────────────────────────────────────────────────────┤
│  Tools ini HANYA untuk:                                     │
│  ✅ Authorized penetration testing                          │
│  ✅ Security research dengan izin                           │
│  ✅ CTF competitions & learning labs                        │
│  ✅ Academic/educational purposes                           │
│                                                              │
│  ILLEGAL DAN DILARANG untuk:                                │
│  ❌ Unauthorized system access                              │
│  ❌ Malicious hacking                                       │
│  ❌ Data theft atau manipulation                            │
│  ❌ Any illegal cyber activities                            │
│                                                              │
│  Author tidak bertanggung jawab atas penyalahgunaan!        │
└─────────────────────────────────────────────────────────────┘
```

---

## 🚨 SECURITY ALERT - CVE-2026-5757

**CRITICAL**: Ollama memiliki vulnerability yang belum di-patch (CVE-2026-5757).

**Mitigasi Required**:
- ✅ NEVER expose port 11434 ke internet
- ✅ Only use models dari verified sources
- ✅ Run Ollama di isolated/trusted network
- ✅ Monitor untuk suspicious model uploads

**Reference**: [GBHackers Security Advisory](https://gbhackers.com/hackers-exploit-ollama-model-uploads-to-leak-server-data/)

---

## 📋 Table of Contents

- [System Requirements](#system-requirements)
- [Quick Start](#quick-start)
- [Detailed Installation](#detailed-installation)
- [Model Selection](#model-selection)
- [Usage Examples](#usage-examples)
- [Project Generation](#project-generation)
- [Troubleshooting](#troubleshooting)
- [Best Practices](#best-practices)
- [Resources](#resources)

---

## 💻 System Requirements

### Minimum Specs
- **OS**: Windows 11 (22H2 or later)
- **RAM**: 16GB
- **VRAM**: 8GB (NVIDIA/AMD)
- **Storage**: 50GB free space
- **Python**: 3.12+

### Recommended Specs (MSI Vector 16 HX)
- **GPU**: RTX 5070 Ti 12GB ✅
- **CPU**: Core Ultra 7 ✅
- **RAM**: 32GB
- **Storage**: NVMe SSD

### Performance Expectations
| Model Size | VRAM Usage | Speed (tokens/sec) | Quality |
|-----------|------------|-------------------|---------|
| 7B        | 6GB        | ~80               | Good    |
| 14B       | 10GB       | ~40               | Better  |
| 32B       | 20GB       | ~20               | Best    |

---

## 🚀 Quick Start

### One-Command Setup
```powershell
# Run automated installer
python setup_offsec_ai.py --auto-install

# Verify installation
python verify_setup.py
```

### Manual 5-Minute Setup
```powershell
# 1. Install Ollama
winget install Ollama.Ollama

# 2. Pull offensive security model
ollama pull xploiter/the-xploiter

# 3. Install Python dependencies
pip install -r requirements.txt

# 4. Configure environment
python configure_env.py

# 5. Test setup
python test_model.py
```

---

## 📦 Detailed Installation

### Phase 1: Base Installation

#### 1.1 Install Ollama
```powershell
# Option A: Using winget (recommended)
winget install Ollama.Ollama

# Option B: Manual download
# Visit: https://ollama.com/download/windows
# Run installer

# Verify
ollama --version
```

#### 1.2 Configure Ollama
```powershell
# Increase context window
setx OLLAMA_CONTEXT_LENGTH 32768

# Set model directory (optional)
setx OLLAMA_MODELS "D:\AI\OllamaModels"

# Restart PowerShell after setx
```

#### 1.3 Verify Ollama
```powershell
# Check if running
curl http://localhost:11434
# Expected: "Ollama is running"

# Check GPU detection
ollama list
```

### Phase 2: Model Installation

#### 2.1 Pull Models
```powershell
# PRIMARY: Offensive Security Specialist
ollama pull xploiter/the-xploiter

# COMPANION: Code Generation
ollama pull qwen2.5-coder:14b

# OPTIONAL: CTF Solver
ollama pull loading_ctf/elona

# OPTIONAL: Fast autocomplete
ollama pull qwen2.5-coder:1.5b
```

#### 2.2 Verify Models
```powershell
# List installed models
ollama list

# Test primary model
ollama run xploiter/the-xploiter "Explain SQL injection testing methodology"
```

### Phase 3: Python Environment

#### 3.1 Install Python
```powershell
# Install Python 3.12
winget install Python.Python.3.12

# Verify
python --version
# Expected: Python 3.12.x
```

#### 3.2 Create Virtual Environment
```powershell
# Create venv
python -m venv C:\Tools\offsec-ai-env

# Activate
C:\Tools\offsec-ai-env\Scripts\activate

# Upgrade pip
python -m pip install --upgrade pip
```

#### 3.3 Install Dependencies
```powershell
# Install from requirements.txt
pip install -r requirements.txt

# Or install individually
pip install aider-chat
pip install ollama
pip install rich
pip install pyyaml
pip install requests
pip install gitpython
```

### Phase 4: Aider Setup

#### 4.1 Install Aider
```powershell
pip install aider-chat

# Verify
aider --version
```

#### 4.2 Configure Aider
Create `.aider.conf.yml` in `%USERPROFILE%`:

```yaml
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
```

---

## 🎯 Model Selection

### Recommended Models for Offensive Security

| Model | Use Case | VRAM | Strengths |
|-------|----------|------|-----------|
| **xploiter/the-xploiter** | Primary offensive sec | 8-10GB | Attack-chain reasoning, exploit validation |
| **xploiter/pentester** | Educational/learning | 6-8GB | Methodology, CTF, labs |
| **qwen2.5-coder:14b** | Code generation | 10GB | Multi-file projects, scaffolding |
| **loading_ctf/elona** | CTF challenges | 8GB | Reverse engineering, crypto |

### Model Comparison

```
Performance (Offensive Security Tasks):
┌─────────────────────────────────────────────────┐
│ xploiter/the-xploiter    ████████████ 92%      │
│ xploiter/pentester       ██████████   85%      │
│ qwen2.5-coder:14b        ████████     75%      │
│ llama3:8b                ████         45%      │
└─────────────────────────────────────────────────┘
```

---

## 💡 Usage Examples

### Example 1: Generate Port Scanner
```powershell
cd C:\Projects\PortScanner
git init
aider --model ollama_chat/xploiter/the-xploiter
```

In Aider:
```
> Create a professional port scanner with:
- TCP/UDP/SYN scan modes
- Service detection and banner grabbing
- Multi-threaded scanning
- JSON output format
- Progress bar
- Rate limiting
- Complete test suite
```

### Example 2: Web Vulnerability Scanner
```powershell
aider --model ollama_chat/xploiter/the-xploiter \
      --message "Create OWASP Top 10 vulnerability scanner"
```

### Example 3: Exploit Development Framework
```powershell
python generate_exploit_framework.py \
    --target "web-applications" \
    --modules "sqli,xss,csrf,xxe,ssrf" \
    --output "./exploit-framework"
```

---

## 🏗️ Project Generation

### Automatic Project Scaffolding

Use `generate_pentest_project.py`:

```powershell
python generate_pentest_project.py \
    --project-type "web-scanner" \
    --name "WebSecScanner" \
    --modules 50 \
    --output "C:\Projects\WebSecScanner"
```

### Supported Project Types
- `web-scanner` - Web application security scanner
- `network-scanner` - Network reconnaissance tool
- `exploit-framework` - Exploit development framework
- `ctf-platform` - CTF challenge platform
- `forensics-toolkit` - Digital forensics tools

### Batch Generation

Generate multiple projects:
```powershell
python batch_generate.py --config projects.yaml
```

`projects.yaml`:
```yaml
projects:
  - name: "WebExploit"
    type: "web-scanner"
    modules: 30
  - name: "NetRecon"
    type: "network-scanner"
    modules: 25
  - name: "ExploitDB"
    type: "exploit-framework"
    modules: 50
```

---

## 🛠️ Troubleshooting

### Issue: Model terlalu lambat
```powershell
# Solution 1: Use smaller model
ollama pull qwen2.5-coder:7b

# Solution 2: Reduce context
# Edit .aider.conf.yml:
num-ctx: 16384  # Instead of 32768

# Solution 3: Check GPU usage
nvidia-smi
```

### Issue: Out of VRAM
```powershell
# Solution 1: Use quantized model
ollama pull xploiter/the-xploiter:q5_K_M

# Solution 2: Close other applications
# Solution 3: Use smaller model
ollama pull xploiter/pentester  # Smaller than the-xploiter
```

### Issue: Ollama not responding
```powershell
# Check service status
Get-Service -Name "Ollama*"

# Restart Ollama
net stop ollama
net start ollama

# Check logs
Get-EventLog -LogName Application -Source Ollama -Newest 10
```

### Issue: Connection refused
```powershell
# Check firewall
netsh advfirewall firewall show rule name="Ollama"

# Allow Ollama
netsh advfirewall firewall add rule name="Ollama" dir=in action=allow protocol=TCP localport=11434

# Test connection
Test-NetConnection -ComputerName localhost -Port 11434
```

---

## 📚 Best Practices

### Security Best Practices
```markdown
✅ DO:
- Always get written authorization before testing
- Document all testing activities
- Use isolated test environments
- Follow responsible disclosure
- Keep tools updated
- Use strong authentication

❌ DON'T:
- Test systems without permission
- Use tools for malicious purposes
- Expose tools/results publicly
- Skip legal compliance
- Ignore scope limitations
```

### Code Quality
```python
# Good: Ethical disclaimer in code
def scan_target(target_url, authorized=False):
    """
    Scan target for vulnerabilities.
    
    IMPORTANT: Only use on authorized targets.
    Unauthorized scanning is illegal.
    """
    if not authorized:
        raise PermissionError("Authorization required")
    
    # Scanning logic...
```

### Performance Optimization
```yaml
# .aider.model.settings.yml
- name: ollama/xploiter/the-xploiter
  num_ctx: 32768      # Large context for complex projects
  num_gpu: 40         # Use GPU layers (adjust for your VRAM)
  num_thread: 8       # CPU threads
  temperature: 0.7    # Balance creativity/consistency
  top_p: 0.9
  top_k: 40
```

---

## 📖 Resources

### Official Documentation
- [Ollama Documentation](https://github.com/ollama/ollama)
- [Aider Documentation](https://aider.chat/docs/)
- [OWASP Testing Guide](https://owasp.org/www-project-web-security-testing-guide/)

### Learning Platforms
- [HackTheBox](https://www.hackthebox.com/) - Pentesting labs
- [TryHackMe](https://tryhackme.com/) - Guided learning
- [PentesterLab](https://pentesterlab.com/) - Web security
- [PortSwigger Web Security Academy](https://portswigger.net/web-security) - Free web security training

### Community
- [Ollama Discord](https://discord.gg/ollama)
- [r/cybersecurity](https://reddit.com/r/cybersecurity)
- [r/netsec](https://reddit.com/r/netsec)
- [OWASP Slack](https://owasp.org/slack/invite)

### Recommended Tools Integration
```bash
# Burp Suite integration
python integrate_burp.py

# Metasploit integration
python integrate_msf.py

# Nmap integration
python integrate_nmap.py
```

---

## 🤝 Contributing

Kontribusi welcome! Silakan:
1. Fork repository
2. Create feature branch
3. Commit changes
4. Push to branch
5. Create Pull Request

---

## 📄 License

MIT License - See LICENSE file for details

---

## 👤 Author

**NuRichter**
- GitHub: [@NuRichter](https://github.com/NuRichter)
- Focus: Cybersecurity, Offensive Security
- Location: Surabaya, Indonesia

---

## 🙏 Acknowledgments

- Ollama team untuk local LLM infrastructure
- Aider team untuk amazing coding assistant
- xploiter untuk offensive security models
- Qwen team untuk excellent code models
- Cybersecurity community

---

## 📊 Project Stats

```
Total Setup Time:     ~30 minutes
Models Downloaded:    ~25GB
Scripts Generated:    15+ ready-to-use
Project Templates:    10+ types
Supported Languages:  Python, JavaScript, Go, Rust, C++
```

---

## 🔄 Updates

### May 2026
- Initial release
- Support for Windows 11
- RTX 5070 Ti optimization
- xploiter/the-xploiter integration

### Planned Features
- [ ] MacOS/Linux support
- [ ] Additional security models
- [ ] GUI interface
- [ ] Cloud deployment options
- [ ] CI/CD templates

---

## ⚡ Quick Reference

### Common Commands
```powershell
# Start Aider
aider --model ollama_chat/xploiter/the-xploiter

# Generate project
python generate_pentest_project.py --type web-scanner

# Test model
python test_model.py

# Verify setup
python verify_setup.py

# Update models
ollama pull xploiter/the-xploiter

# Check logs
python show_logs.py
```

### Hotkeys (Aider)
- `/add` - Add files to context
- `/drop` - Remove files from context
- `/diff` - Show changes
- `/commit` - Commit changes
- `/undo` - Undo last change
- `/help` - Show help
- `/exit` - Exit Aider

---

**Remember**: With great power comes great responsibility. Use these tools ethically and legally! 🔐

---

*Last updated: May 4, 2026*
