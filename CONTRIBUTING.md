# 🧩 Contributing to Satori

Thank you for your interest in contributing to **Satori**, a framework for building proactive AR task guidance systems.

We welcome contributions in all forms — from bug reports and documentation improvements to new pipeline components.

---

## 🚀 Getting Started

To set up the development environment:

```bash
# Clone the repository
git clone https://github.com/VIDA-NYU/satori-assistance.git
cd satori-assistance

# Set up virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows, use `.venv\Scripts\activate`

# Install dependencies
pip install -r requirements.txt
```

To run the system:

```bash
python main.py
```

Pipeline and agent configurations are located in the `configs/` directory.

---

## 🧪 Testing

We recommend creating a test agent and pipeline config for your changes. Automated testing support is in progress. Please test locally using:

```bash
python main.py
```

---

## 📐 Coding Guidelines

- Use clear and descriptive naming
- Add inline comments and docstrings for public classes and methods
- Follow PEP8 standards (you can use tools like `black` or `ruff`)

---

## 📥 How to Contribute

1. Fork the repository and create a new branch for your feature or fix.
2. Commit your changes with a clear message.
3. Push to your fork and open a pull request (PR) to the `main` branch.
4. Include context and screenshots (if relevant) in your PR.

---

## 🐛 Reporting Issues

If you encounter a bug or have a feature request, please [open an issue](https://github.com/VIDA-NYU/satori-assistance/issues) with:
- A clear title
- Steps to reproduce (if a bug)
- Suggested improvement (if a feature)

---

## 🙏 Acknowledgments

This project is developed at [VIDA Lab @ NYU](https://vida.engineering.nyu.edu/). We appreciate your help in improving the system.

By contributing, you agree that your contributions will be licensed under the MIT License.
