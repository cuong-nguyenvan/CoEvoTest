# Collected Policies

This directory should contain the 591 XACML policy files used in the experiments.
The policies are sourced from three public datasets:

## Download Sources

| Dataset | Policies | Source |
|-----------|--------:|--------|
| AuthzForce | 545 | [AuthzForce/core (GitHub)](https://github.com/authzforce/core) — OASIS XACML 2.0/3.0 conformance tests |
| DyPol | 41 | [DyPol Dataset](https://github.com/dianxiangxu/XPA) — Dynamic policy benchmarks |
| ONAP | 5 | [ONAP Policy Framework](https://github.com/onap/policy-xacml-pdp) — Network automation policies |

## Expected Structure

```
collected_policies/
├── metadata.json
├── authzforce/
│   ├── *.xml          (545 files)
├── dypol/
│   ├── *.xml          (41 files)
└── onap/
    ├── *.xml          (5 files)
```

## Note

The pre-computed experimental results in `results/` were generated from these 591 policies.
You only need to download the policies if you want to **re-run** the experiments.
To reproduce figures from existing results, simply run:

```bash
python experiments/plot_results.py
```
