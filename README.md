# CoEvoTest: Co-Evolutionary Test Case Generation for XACML Policies

Official implementation and experimental artifacts for the paper:

> **CoEvoTest: A Co-Evolutionary Approach to Automated Test Case Generation for XACML Access Control Policies**

CoEvoTest is a co-evolutionary genetic algorithm framework for automated test case generation targeting XACML (eXtensible Access Control Markup Language) access control policies. The framework co-evolves test suites and policy mutants to maximize rule coverage, test diversity, and fitness, outperforming existing baselines including JCSCE (XFG-GA) and Random testing.

---

## Features

- Co-evolutionary GA engine with dual-population evolution (test suites & policy mutants)
- XACML policy parser supporting XACML 2.0/3.0 specifications
- Multi-objective fitness function: coverage (w1) + diversity (w2) + suite compactness (w3)
- JCSCE (XFG-GA) baseline implementation for comparison
- Random baseline for lower-bound benchmarking
- Robustness evaluation via policy mutation testing (5 mutation operators)
- Convergence history tracking per generation
- Academic-quality figure generation (6 publication-ready plots)
- Evaluated on 591 real-world XACML policies across 3 datasets

---

## Benchmark

The benchmark comprises 591 real-world XACML policies from three public datasets.

| Dataset | Policies | Description |
|-----------|--------:|------------------------------------|
| AuthzForce | 545 | OASIS XACML conformance test suite |
| DyPol | 41 | Dynamic policy management system |
| ONAP | 5 | Open Network Automation Platform |
| **Total** | **591** | |

The policies are located in the `collected_policies/` directory.

---

## Repository Structure

```text
CoEvoTest/
│
├── src/                           # Source code
│   ├── parser/
│   │   └── xacml_parser.py        # XACML policy parser
│   ├── coevolution/
│   │   └── coevolution_engine.py  # Co-evolutionary GA engine
│   ├── baseline/
│   │   ├── random_baseline.py     # Random test generation baseline
│   │   └── jcsce_baseline.py      # JCSCE (XFG-GA) baseline
│   └── mutator/
│       └── policy_mutator.py      # XACML policy mutation operators
│
├── collected_policies/            # XACML benchmark policies (see README inside)
│   └── README.md                  # Download instructions for 591 policies
│
├── experiments/                   # Scripts for reproducing experiments
│   ├── run_experiments.py         # Main experiment runner
│   └── plot_results.py            # Academic figure generation
│
├── results/                       # Experimental results
│   ├── figures/                   # Publication-ready figures (PNG + PDF)
│   ├── history.zip                # Per-policy convergence history (1,431 CSVs, compressed)
│   ├── results.csv                # Detailed results for all 591 policies
│   ├── summary.csv                # Aggregated results by dataset
│   └── robustness.csv             # Robustness evaluation (mutation testing)
│
├── requirements.txt
├── README.md
└── LICENSE
```

---

## Installation

### Clone repository

```bash
git clone https://github.com/binhtt/CoEvoTest.git
cd CoEvoTest
```

### Install dependencies

```bash
pip install -r requirements.txt
```

---

## Usage

### Reproduce figures from existing results (no policy download needed)

The repository includes pre-computed results for all 591 policies. To generate all 6 publication-ready figures directly:

```bash
python experiments/plot_results.py
```

### Re-run experiments from scratch

> **Note:** To re-run experiments, you must first download the 591 XACML policies into `collected_policies/`. See [`collected_policies/README.md`](collected_policies/README.md) for download instructions.

Run the complete experimental evaluation:

```bash
python experiments/run_experiments.py
```

For a quick test with a subset of policies:

```bash
python experiments/run_experiments.py --max-policies 30
```

Available options:

| Argument | Default | Description |
|---------------------|---------|--------------------------------------|
| `--max-policies` | None | Limit number of policies (quick test) |
| `--generations` | 15 | Number of GA generations |
| `--pop-size` | 10 | Population size |
| `--suite-size` | 15 | Test suite size |
| `--n-trials` | 200 | Number of random baseline trials |
| `--seed` | 42 | Random seed for reproducibility |
| `--save-history` | True | Save per-generation convergence data |

### Experiment 2: Robustness evaluation

Automatically runs after Experiment 1. Selects the 10 most complex policies, generates 5 mutated versions (V1–V5) per policy, and evaluates how well the original test suites maintain coverage on mutated policies.

### Generate figures

After running experiments, generate all 6 publication-ready figures:

```bash
python experiments/plot_results.py
```

Generated figures:

| Figure | Description |
|--------|----------------------------------------------|
| Fig 1 | Fitness comparison: CoEvo vs JCSCE vs Random |
| Fig 2 | Complexity analysis (rules vs fitness) |
| Fig 3 | Improvement of CoEvo over JCSCE (%) |
| Fig 4 | Fitness distribution box plot (AuthzForce) |
| Fig 5 | Convergence comparison across generations |
| Fig 6 | Robustness across mutated policy versions |

---

## Experimental Results

### Average performance across datasets

| Dataset | N | CoEvo Fitness | JCSCE Fitness | Random Fitness | Improvement vs JCSCE |
|-----------|----:|:-------------:|:-------------:|:--------------:|:--------------------:|
| AuthzForce | 545 | **0.9268** | 0.8369 | 0.8142 | +11.46% |
| DyPol | 41 | **0.9074** | 0.8530 | 0.8331 | +7.80% |
| ONAP | 5 | **0.8566** | 0.7075 | 0.6777 | +21.51% |

### Key findings

- CoEvoTest achieves **100% rule coverage** across all 591 policies in all three datasets
- Average fitness improvement of **+11.46%** over JCSCE on AuthzForce (largest dataset)
- Up to **+21.51%** improvement on complex ONAP policies
- Robust test suites maintain high coverage under policy mutations (V0–V5)

---

## Output Files

| File | Description |
|------------------------|-----------------------------------------|
| `results/results.csv` | Per-policy metrics for all 591 policies |
| `results/summary.csv` | Aggregated averages by dataset |
| `results/robustness.csv` | Coverage retention under policy mutations |
| `results/figures/` | 6 academic figures in PNG and PDF format |
| `results/history.zip` | Per-generation fitness convergence logs (unzip before use) |

---

## Technologies

- Python 3.10+
- NumPy
- Matplotlib
- Standard library: csv, json, argparse, pathlib

---

## Citation

If you use this repository, please cite:

```bibtex
@article{Thanh2026CoEvoTest,
  title     = {CoEvoTest: A Co-Evolutionary Approach to Automated Test Case
               Generation for XACML Access Control Policies},
  author    = {Trinh, Thanh Binh},
  year      = {2026}
}
```

---

## License

This project is distributed under the MIT License. See [LICENSE](LICENSE) for details.

---

## Contact

**Binh Trinh Thanh**
Faculty of Information Systems
Phenikaa University, Hanoi, Vietnam

Email: binh.trinhthanh@phenikaa-uni.edu.vn
