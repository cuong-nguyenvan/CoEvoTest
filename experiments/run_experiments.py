"""
run_experiments.py

Chay toan bo thi nghiem: Co-evolutionary GA vs JCSCE Baseline vs Random Baseline
tren cac XACML policies tu 3 dataset (authzforce, dypol, onap).

Ket qua luu vao:
    results/results.csv       -- bang so lieu tinh (Experiment 1)
    results/summary.csv       -- tong hop theo dataset
    results/robustness.csv    -- so lieu do ben kiem thu (Experiment 2)
    results/history/          -- lich su fitness theo generation cua CoEvoTest va JCSCE

Cach chay:
    python run_experiments.py
    python run_experiments.py --max-policies 30   # chay nhanh
"""

import argparse
import csv
import json
import os
import sys
import time
import copy
from pathlib import Path

CURRENT_DIR = Path(__file__).parent
ROOT = CURRENT_DIR.parent
sys.path.insert(0, str(ROOT))

from src.parser.xacml_parser import XACMLParser, get_all_rules
from src.coevolution.coevolution_engine import CoEvolutionEngine
from src.baseline.random_baseline import RandomBaseline
from src.baseline.jcsce_baseline import JCSCEBaseline
from src.mutator.policy_mutator import PolicyMutator

# ── Cau hinh mac dinh ─────────────────────────────────────────────────────────

DEFAULTS = dict(
    generations  = 15,
    pop_size     = 10,
    suite_size   = 15,
    n_trials     = 200,   # so lan thu cua random baseline
    w1           = 0.5,
    w2           = 0.3,
    w3           = 0.2,
    max_suite    = 50,
    seed         = 42,
)

RESULTS_DIR      = ROOT / "results"
RESULTS_CSV      = RESULTS_DIR / "results.csv"
SUMMARY_CSV      = RESULTS_DIR / "summary.csv"
ROBUSTNESS_CSV   = RESULTS_DIR / "robustness.csv"
HISTORY_DIR      = RESULTS_DIR / "history"

FIELDNAMES = [
    "policy_id", "dataset", "num_rules",
    "ga_fitness", "ga_coverage", "ga_diversity", "ga_suite_size", "ga_time_s",
    "jcsce_fitness", "jcsce_coverage", "jcsce_diversity", "jcsce_suite_size", "jcsce_time_s",
    "rand_fitness", "rand_coverage", "rand_diversity", "rand_suite_size", "rand_time_s",
    "improvement_rand",  # (ga_fitness - rand_fitness) / rand_fitness * 100
    "improvement_jcsce", # (ga_fitness - jcsce_fitness) / jcsce_fitness * 100
]


# ── Tien ich ──────────────────────────────────────────────────────────────────

def load_metadata(policies_dir: Path) -> list[dict]:
    meta_path = policies_dir / "metadata.json"
    if meta_path.exists():
        with open(meta_path, encoding="utf-8") as f:
            return json.load(f)
    # Fallback
    entries = []
    for xml_file in sorted(policies_dir.rglob("*.xml")):
        dataset = xml_file.parent.name
        entries.append({
            "policy_id": xml_file.stem,
            "dataset":   dataset,
            "path":      str(xml_file),
            "num_rules": -1,
        })
    return entries


def run_one_policy(entry: dict, cfg: dict) -> dict | None:
    """Chay GA + JCSCE + Random cho 1 policy."""
    path = entry.get("path", "")
    if not path:
        collected_as = entry.get("collected_as", "")
        dataset      = entry.get("source", entry.get("dataset", ""))
        if collected_as:
            path = str(ROOT / "collected_policies" / dataset / collected_as)
        else:
            policy_id = entry.get("policy_id", "")
            path = str(ROOT / "collected_policies" / dataset / f"{policy_id}.xml")

    if not os.path.exists(path):
        return None

    parser = XACMLParser()
    try:
        ast = parser.parse(path)
    except Exception:
        return None

    if ast is None:
        return None

    num_rules = entry.get("num_rules", -1)
    if num_rules <= 0:
        num_rules = len(get_all_rules(ast))

    if num_rules == 0:
        return None   # Bo qua policy khong co rule

    # ── 1. Co-evolutionary GA (CoEvoTest) ─────────────────────────────────────
    t0 = time.perf_counter()
    engine = CoEvolutionEngine(
        seed=cfg["seed"], w1=cfg["w1"], w2=cfg["w2"], w3=cfg["w3"],
        max_suite_size=cfg["max_suite"],
    )
    ga_result = engine.run(
        ast,
        generations = cfg["generations"],
        pop_size    = cfg["pop_size"],
        suite_size  = cfg["suite_size"],
        verbose     = False,
    )
    ga_time = round(time.perf_counter() - t0, 3)

    # ── 2. JCSCE Baseline (Graph DFS + Single-Pop GA) ──────────────────────────
    t0 = time.perf_counter()
    jcsce = JCSCEBaseline(
        seed=cfg["seed"], w1=cfg["w1"], w2=cfg["w2"], w3=cfg["w3"],
        max_suite_size=cfg["max_suite"],
    )
    jcsce_result = jcsce.run(
        ast,
        generations = cfg["generations"],
        pop_size    = cfg["pop_size"],
        suite_size  = cfg["suite_size"],
        verbose     = False,
    )
    jcsce_time = round(time.perf_counter() - t0, 3)

    # ── 3. Random Baseline ───────────────────────────────────────────────────
    t0 = time.perf_counter()
    baseline = RandomBaseline(
        seed=cfg["seed"], w1=cfg["w1"], w2=cfg["w2"], w3=cfg["w3"],
        max_suite_size=cfg["max_suite"],
    )
    rand_result = baseline.run(ast, suite_size=cfg["suite_size"], n_trials=cfg["n_trials"])
    rand_time = round(time.perf_counter() - t0, 3)

    # ── Tinh improvements ─────────────────────────────────────────────────────
    if rand_result.best_fitness > 0:
        improvement_rand = round(
            (ga_result.best_fitness - rand_result.best_fitness) / rand_result.best_fitness * 100, 2
        )
    else:
        improvement_rand = 0.0

    if jcsce_result.best_fitness > 0:
        improvement_jcsce = round(
            (ga_result.best_fitness - jcsce_result.best_fitness) / jcsce_result.best_fitness * 100, 2
        )
    else:
        improvement_jcsce = 0.0

    return {
        "policy_id":      entry.get("collected_as", entry.get("policy_id", "")),
        "dataset":        entry.get("source", entry.get("dataset", "")),
        "num_rules":      num_rules,
        "ga_fitness":     ga_result.best_fitness,
        "ga_coverage":    ga_result.best_coverage,
        "ga_diversity":   ga_result.best_diversity,
        "ga_suite_size":  len(ga_result.best_test_suite),
        "ga_time_s":      ga_time,
        "jcsce_fitness":  jcsce_result.best_fitness,
        "jcsce_coverage": jcsce_result.best_coverage,
        "jcsce_diversity":jcsce_result.best_diversity,
        "jcsce_suite_size": len(jcsce_result.best_test_suite),
        "jcsce_time_s":   jcsce_time,
        "rand_fitness":   rand_result.best_fitness,
        "rand_coverage":  rand_result.best_coverage,
        "rand_diversity": rand_result.best_diversity,
        "rand_suite_size": rand_result.best_suite_size,
        "rand_time_s":    rand_time,
        "improvement_rand":  improvement_rand,
        "improvement_jcsce": improvement_jcsce,
        "_ga_history":       ga_result.history,
        "_jcsce_history":    jcsce_result.history,
        "_ga_suite":         ga_result.best_test_suite,
        "_jcsce_suite":      jcsce_result.best_test_suite,
        "_ast":              ast,
    }


def _safe_filename(name: str) -> str:
    import re
    return re.sub(r'[\\/:*?"<>|]', '_', name)[:80]


def save_histories(policy_id: str, ga_history: list, jcsce_history: list, history_dir: Path) -> None:
    """Luu lich su fitness theo generation ra file CSV."""
    history_dir.mkdir(parents=True, exist_ok=True)
    
    # Save GA history
    ga_path = history_dir / f"history_ga_{_safe_filename(policy_id)}.csv"
    with open(ga_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "generation", "best_test_fit", "best_policy_fit", "avg_test_fit", "best_coverage", "best_diversity", "best_suite_size"
        ])
        writer.writeheader()
        for log in ga_history:
            writer.writerow({
                "generation":      log.generation,
                "best_test_fit":   log.best_test_fit,
                "best_policy_fit": log.best_policy_fit,
                "avg_test_fit":    log.avg_test_fit,
                "best_coverage":   log.best_coverage,
                "best_diversity":  log.best_diversity,
                "best_suite_size": log.best_suite_size,
            })

    # Save JCSCE history
    jcsce_path = history_dir / f"history_jcsce_{_safe_filename(policy_id)}.csv"
    with open(jcsce_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "generation", "best_test_fit", "avg_test_fit", "best_coverage", "best_diversity", "best_suite_size"
        ])
        writer.writeheader()
        for log in jcsce_history:
            writer.writerow({
                "generation":      log.generation,
                "best_test_fit":   log.best_test_fit,
                "avg_test_fit":    log.avg_test_fit,
                "best_coverage":   log.best_coverage,
                "best_diversity":  log.best_diversity,
                "best_suite_size": log.best_suite_size,
            })


def compute_summary(rows: list[dict]) -> list[dict]:
    """Tong hop ket qua theo dataset."""
    from collections import defaultdict
    groups: dict[str, list] = defaultdict(list)
    for r in rows:
        groups[r["dataset"]].append(r)

    summary = []
    for dataset, group in sorted(groups.items()):
        n = len(group)
        def avg(key): return round(sum(r[key] for r in group) / n, 4)
        summary.append({
            "dataset":             dataset,
            "n_policies":          n,
            "avg_ga_fitness":      avg("ga_fitness"),
            "avg_jcsce_fitness":   avg("jcsce_fitness"),
            "avg_rand_fitness":    avg("rand_fitness"),
            "avg_improvement_rand":  avg("improvement_rand"),
            "avg_improvement_jcsce": avg("improvement_jcsce"),
            "avg_ga_coverage":     avg("ga_coverage"),
            "avg_jcsce_coverage":  avg("jcsce_coverage"),
            "avg_rand_coverage":   avg("rand_coverage"),
            "avg_ga_suite_size":   avg("ga_suite_size"),
            "avg_jcsce_suite_size":  avg("jcsce_suite_size"),
            "avg_rand_suite_size":   avg("rand_suite_size"),
            "avg_ga_time_s":       avg("ga_time_s"),
            "avg_jcsce_time_s":    avg("jcsce_time_s"),
        })
    return summary


# ── Thực nghiệm 2: Đánh giá độ bền bỉ khi policy biến đổi (Robustness) ─────────

def run_robustness_experiment(selected_policies: list[dict], cfg: dict):
    """
    Thuc nghiem 2:
    - Lay bo test suite toi uu cua CoEvoTest va JCSCE cho policy goc P_0.
    - Tao ra 5 bien the dot bien P_1 ... P_5 cua policy.
    - Chay hai bo test cu va do do sut giam coverage.
    """
    print("\n" + "=" * 70)
    print("BAT DAU THUC NGHIEM 2: KIEM THU HOI QUY DONG (ROBUSTNESS EVALUATION)")
    print("=" * 70)
    
    mutator = PolicyMutator(seed=cfg["seed"])
    engine = CoEvolutionEngine(w1=cfg["w1"], w2=cfg["w2"], w3=cfg["w3"]) # De evaluate
    
    robustness_results = []
    
    for i, res in enumerate(selected_policies, 1):
        pid = res["policy_id"]
        dataset = res["dataset"]
        print(f"[{i:>2}/{len(selected_policies)}] Mutation testing for {pid} (rules={res['num_rules']})...")
        
        ast_root = res["_ast"]
        ga_suite = res["_ga_suite"]
        jcsce_suite = res["_jcsce_suite"]
        
        # P_0: Coverage goc
        ga_cov_0 = res["ga_coverage"]
        jcsce_cov_0 = res["jcsce_coverage"]
        
        robustness_results.append({
            "policy_id": pid,
            "dataset": dataset,
            "version": "V0 (Original)",
            "ga_coverage": ga_cov_0,
            "jcsce_coverage": jcsce_cov_0,
        })
        
        # Tao 5 phien ban bien the
        # Moi phien ban ke tiep duoc tao bang cach mutate tu phien ban truoc (tich luy dot bien)
        current_ast = ast_root
        for v in range(1, 6):
            # Mutate
            current_ast, op = mutator.mutate(current_ast)
            
            # Evaluate test suite cu tren policy bien the moi
            res_ga = engine.evaluator.evaluate(ga_suite, current_ast)
            res_jcsce = engine.evaluator.evaluate(jcsce_suite, current_ast)
            
            robustness_results.append({
                "policy_id": pid,
                "dataset": dataset,
                "version": f"V{v} ({op})",
                "ga_coverage": res_ga.coverage,
                "jcsce_coverage": res_jcsce.coverage,
            })
            
    # Ghi ket qua robustness vao file CSV
    with open(ROBUSTNESS_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["policy_id", "dataset", "version", "ga_coverage", "jcsce_coverage"])
        writer.writeheader()
        writer.writerows(robustness_results)
        
    print(f"Robustness results saved to: {ROBUSTNESS_CSV}")


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Run Co-evolutionary GA vs JCSCE experiments")
    parser.add_argument("--max-policies", type=int, default=None,
                        help="Gioi han so policy de thu nghiem nhanh")
    parser.add_argument("--generations",  type=int, default=DEFAULTS["generations"])
    parser.add_argument("--pop-size",     type=int, default=DEFAULTS["pop_size"])
    parser.add_argument("--suite-size",   type=int, default=DEFAULTS["suite_size"])
    parser.add_argument("--n-trials",     type=int, default=DEFAULTS["n_trials"])
    parser.add_argument("--seed",         type=int, default=DEFAULTS["seed"])
    parser.add_argument("--save-history", action="store_true", default=True,
                        help="Luu lich su fitness theo generation")
    args = parser.parse_args()

    cfg = {
        "generations": args.generations,
        "pop_size":    args.pop_size,
        "suite_size":  args.suite_size,
        "n_trials":    args.n_trials,
        "w1": DEFAULTS["w1"], "w2": DEFAULTS["w2"], "w3": DEFAULTS["w3"],
        "max_suite": DEFAULTS["max_suite"],
        "seed": args.seed,
    }

    # Tao cac thu muc ket qua
    RESULTS_DIR.mkdir(exist_ok=True)
    HISTORY_DIR.mkdir(exist_ok=True)

    policies_dir = ROOT / "collected_policies"
    entries = load_metadata(policies_dir)

    if args.max_policies:
        entries = entries[:args.max_policies]

    total = len(entries)
    print(f"Bat dau thi nghiem: {total} policies")
    print(f"Config: generations={cfg['generations']}, pop_size={cfg['pop_size']}, "
          f"suite_size={cfg['suite_size']}, n_trials={cfg['n_trials']}")
    print("-" * 80)

    rows = []
    skipped = 0
    
    # Danh sach tat ca cac policy chay thanh cong de chon robustness candidates cuoi cung
    all_evaluated_cache = []

    with open(RESULTS_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writeheader()

        for i, entry in enumerate(entries, 1):
            pid = entry.get("policy_id", f"policy_{i}")
            print(f"[{i:>4}/{total}] {pid:<30}", end=" ", flush=True)

            try:
                row = run_one_policy(entry, cfg)
            except Exception as e:
                import traceback
                print(f"ERROR: {e}")
                traceback.print_exc()
                skipped += 1
                continue

            if row is None:
                print("SKIP (no rules / invalid)")
                skipped += 1
                continue

            # Rut lay thong tin tam thoi de ghi CSV va luu history
            ga_hist = row.pop("_ga_history", [])
            jcsce_hist = row.pop("_jcsce_history", [])
            
            # Luu vao cache de chon candidates thuc nghiem 2
            all_evaluated_cache.append({
                "policy_id": row["policy_id"],
                "dataset": row["dataset"],
                "num_rules": row["num_rules"],
                "ga_coverage": row["ga_coverage"],
                "jcsce_coverage": row["jcsce_coverage"],
                "_ga_suite": row["_ga_suite"],
                "_jcsce_suite": row["_jcsce_suite"],
                "_ast": row["_ast"]
            })

            # Clear truoc khi ghi CSV
            row.pop("_ga_suite", None)
            row.pop("_jcsce_suite", None)
            row.pop("_ast", None)

            if args.save_history:
                save_histories(pid, ga_hist, jcsce_hist, HISTORY_DIR)

            writer.writerow(row)
            f.flush()
            rows.append(row)

            print(f"CoEvo={row['ga_fitness']:.4f}  "
                  f"JCSCE={row['jcsce_fitness']:.4f}  "
                  f"Rand={row['rand_fitness']:.4f}  "
                  f"+{row['improvement_jcsce']:.1f}% vs JCSCE  "
                  f"({row['ga_time_s']}s)")

    # ── Thực nghiệm 2 (Robustness/Regression) ─────────────────────────────────
    # Sap xep theo do phuc tap (num_rules) giam dan va chon ra 10 policy
    robustness_candidates = sorted(all_evaluated_cache, key=lambda x: x["num_rules"], reverse=True)[:10]
    
    if robustness_candidates:
        run_robustness_experiment(robustness_candidates, cfg)
    else:
        print("Khong co du candidate hop le de chay Thuc nghiem 2.")

    # Tong hop ket qua (summary.csv)
    if rows:
        summary = compute_summary(rows)
        with open(SUMMARY_CSV, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=list(summary[0].keys()))
            writer.writeheader()
            writer.writerows(summary)

        print("\n" + "=" * 90)
        print(f"TONG KET: {len(rows)} policies thanh cong, {skipped} bo qua")
        print(f"Ket qua: {RESULTS_CSV}")
        print(f"Tong hop: {SUMMARY_CSV}")
        print()
        print(f"  {'Dataset':<15} {'N':>5} {'CoEvo_Fit':>9} {'JCSCE_Fit':>9} {'Rand_Fit':>9} {'Improv_JCSCE':>12} {'CoEvo_Cov':>9} {'JCSCE_Cov':>9}")
        print(f"  {'-'*85}")
        for s in summary:
            print(f"  {s['dataset']:<15} {s['n_policies']:>5} "
                  f"{s['avg_ga_fitness']:>9.4f} {s['avg_jcsce_fitness']:>9.4f} {s['avg_rand_fitness']:>9.4f} "
                  f"{s['avg_improvement_jcsce']:>11.2f}% {s['avg_ga_coverage']:>9.4f} {s['avg_jcsce_coverage']:>9.4f}")
    else:
        print("Khong co ket qua nao duoc ghi.")


if __name__ == "__main__":
    main()
