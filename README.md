# 🧠 Satori: Proactive AR Task Guidance Framework

Satori is a modular framework for developing context-aware augmented reality (AR) task assistants. It enables real-time, step-by-step guidance by integrating egocentric vision, stream-based data pipelines, and language-based reasoning.

Designed for AR devices like Microsoft HoloLens, Satori allows researchers and developers to prototype and deploy intelligent AR systems with reusable components.

<!-- [![License](https://img.shields.io/github/license/VIDA-NYU/satori-assistance)](./LICENSE)   -->
![MIT](https://img.shields.io/badge/license-MIT-green)
<!-- 📄 [CHI '25 Paper (ACM DL)](https://link-to-chi-paper.com) •  -->
📄 *Satori: Towards Proactive AR Assistant with Belief-Desire-Intention User Modeling* — Accepted to **ACM CHI 2025**. [arXiv](https://arxiv.org/abs/2410.16668)
<!-- [CHI Paper](https://link-to-chi-paper.com) •  -->
<!-- 🔬 [arXiv Preprint](https://arxiv.org/abs/2410.16668) -->

---

## 🧭 Features

- Stream-based architecture using `ptgctl`
- Modular pipeline system for vision, reasoning, and feedback
- Agent abstraction for composing AR task logic
- Integration with GPT-4V for multimodal guidance generation
- Flexible configuration via YAML

---

## 🚀 Getting Started

### Requirements

- Python 3.9+
- PyTorch + torchvision
- `ptgctl` and `ptgctl-pipeline`
- Additional dependencies in `requirements.txt`

### Installation

```bash
# Clone the repository
git clone https://github.com/VIDA-NYU/satori-assistance.git
cd satori-assistance

# Create virtual environment (optional but recommended)
python -m venv .venv
source .venv/bin/activate  # on Windows use `.venv\Scripts\activate`

# Install dependencies
pip install -r requirements.txt
```

### Run the Application

```bash
python main.py
```

By default, this launches the main Satori agent using pipeline configurations located in the [`configs/`](./configs/) folder. You can modify these to define your own tasks and pipeline compositions.

---

## 📁 Project Structure

```
satori-assistance/
├── main.py                     # Main entry point
├── configs/                    # Pipeline and agent configuration files
├── pipelines/                 # Pipeline logic (e.g., belief, desire, guidance)
├── ptgctl_pipeline/           # Stream management and base classes
├── docs/                      # Sphinx documentation
├── requirements.txt           # Python dependencies
└── README.md                  # This file
```

---

## 🔧 Configuration

You can customize the task agent using YAML config files in `configs/`. These specify:

- Pipelines to load (e.g., task control, guidance, vision)
- Stream mappings
- Optional runtime parameters

Refer to [`configs/README.md`](./configs/README.md) for examples.

---

## 📚 Documentation

Full documentation is available at:

📘 [Satori Documentation](https://your-docs-link.com)

To build the docs locally:

```bash
cd docs
make html
```

---

## 📄 Citation

If you use Satori in your research or applications, please cite our CHI 2025 paper:

```
@article{li2024satori,
  title={Satori: Towards Proactive AR Assistant with Belief-Desire-Intention User Modeling},
  author={Li, Chenyi and Wu, Guande and Chan, Gromit Yeuk-Yin and Turakhia, Dishita G and Quispe, Sonia Castelo and Li, Dong and Welch, Leslie and Silva, Claudio and Qian, Jing},
  journal={arXiv preprint arXiv:2410.16668},
  year={2024}
}
```

---

## 🧑‍💻 Contributing

We welcome contributions! Please see [CONTRIBUTING.md](./CONTRIBUTING.md) for guidelines and open issues.

---

## 🛠️ Maintainers

Developed by [VIDA Lab @ NYU](https://vida.engineering.nyu.edu/)  
Contact: [Guande Wu](https://www.gdwu.xyz)

---

## 📬 License

This project is licensed under the MIT License. See [LICENSE](./LICENSE) for details.
