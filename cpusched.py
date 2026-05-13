import tkinter as tk
from tkinter import ttk, messagebox

# ─── Color Palette ────────────────────────────────────────────────────────────
BG       = "#d0d0d0"
PANEL_BG = "#e8e8e8"
HEADER   = "#4a4a4a"
TEAL     = "#00bcd4"
TEAL_DK  = "#0097a7"
WHITE    = "#ffffff"
DARK     = "#2e2e2e"
ROW_ALT  = "#f0f0f0"
ROW_EVEN = "#fafafa"
TEXT_LT  = "#ffffff"
TEXT_DK  = "#222222"

PROCESS_COLORS = ["#00bcd4","#26a69a","#7e57c2","#ef5350","#ffa726","#66bb6a","#ab47bc","#5c6bc0"]

# ─── Scheduling Algorithms ────────────────────────────────────────────────────

def run_fcfs(processes):
    procs = sorted(processes, key=lambda p: (p["arrival"], p["pid"]))
    time = 0
    timeline = []
    results = {}
    for p in procs:
        if time < p["arrival"]:
            time = p["arrival"]
        start = time
        end = time + p["burst"]
        timeline.append({"pid": p["pid"], "start": start, "end": end})
        results[p["pid"]] = {"turnaround": end - p["arrival"], "waiting": start - p["arrival"]}
        time = end
    return timeline, results

def run_sjf(processes):
    procs = [dict(p) for p in processes]
    time = 0
    timeline = []
    results = {}
    done = set()
    while len(done) < len(procs):
        available = [p for p in procs if p["arrival"] <= time and p["pid"] not in done]
        if not available:
            time += 1
            continue
        p = min(available, key=lambda x: (x["burst"], x["arrival"]))
        start = time
        end = time + p["burst"]
        timeline.append({"pid": p["pid"], "start": start, "end": end})
        results[p["pid"]] = {"turnaround": end - p["arrival"], "waiting": start - p["arrival"]}
        time = end
        done.add(p["pid"])
    return timeline, results

def run_priority(processes):
    procs = [dict(p) for p in processes]
    time = 0
    timeline = []
    results = {}
    done = set()
    while len(done) < len(procs):
        available = [p for p in procs if p["arrival"] <= time and p["pid"] not in done]
        if not available:
            time += 1
            continue
        p = min(available, key=lambda x: (x["priority"], x["arrival"]))
        start = time
        end = time + p["burst"]
        timeline.append({"pid": p["pid"], "start": start, "end": end})
        results[p["pid"]] = {"turnaround": end - p["arrival"], "waiting": start - p["arrival"]}
        time = end
        done.add(p["pid"])
    return timeline, results

def run_srtf(processes):
    procs = [dict(p, remaining=p["burst"]) for p in processes]
    time = 0
    timeline = []
    results = {}
    last_pid = None
    seg_start = 0
    total_time = sum(p["burst"] for p in procs)
    finish_time = max(p["arrival"] for p in procs) + total_time + 1

    for t in range(finish_time):
        available = [p for p in procs if p["arrival"] <= t and p["remaining"] > 0]
        if not available:
            if last_pid is not None:
                timeline.append({"pid": last_pid, "start": seg_start, "end": t})
                last_pid = None
            continue
        p = min(available, key=lambda x: (x["remaining"], x["arrival"]))
        if p["pid"] != last_pid:
            if last_pid is not None:
                timeline.append({"pid": last_pid, "start": seg_start, "end": t})
            last_pid = p["pid"]
            seg_start = t
        p["remaining"] -= 1
        if p["remaining"] == 0:
            end = t + 1
            timeline.append({"pid": p["pid"], "start": seg_start, "end": end})
            results[p["pid"]] = {"turnaround": end - p["arrival"], "waiting": end - p["arrival"] - p["burst"]}
            last_pid = None
            seg_start = end
        if all(p["remaining"] == 0 for p in procs):
            break

    merged = []
    for seg in timeline:
        if merged and merged[-1]["pid"] == seg["pid"] and merged[-1]["end"] == seg["start"]:
            merged[-1]["end"] = seg["end"]
        else:
            merged.append(dict(seg))
    return merged, results


# ─── Main Application ─────────────────────────────────────────────────────────

class CPUSchedulerApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("CPU Scheduling")
        self.configure(bg=BG)
        self.resizable(True, True)
        self.geometry("1100x680")

        self.algorithm_var = tk.StringVar(value="FCFS")
        self.n_var = tk.StringVar(value="4")
        self.job_rows = []

        self._build_ui()
        self._add_default_jobs()

    # ── UI Construction ────────────────────────────────────────────────────────

    def _build_ui(self):
        # ── Header ──
        hdr = tk.Frame(self, bg=HEADER)
        hdr.pack(fill="x")
        tk.Label(hdr, text="CPU Scheduling", font=("Georgia", 26, "bold"),
                 bg=HEADER, fg=WHITE, padx=20, pady=14).pack(anchor="w")

        # ── Main area ──
        main = tk.Frame(self, bg=BG)
        main.pack(fill="both", expand=True, padx=20, pady=10)

        # Left: Settings panel
        left = tk.Frame(main, bg=PANEL_BG, bd=0, relief="flat",
                        highlightthickness=1, highlightbackground="#b0b0b0")
        left.pack(side="left", fill="y", padx=(0, 12), pady=4, ipadx=12, ipady=12)
        self._build_settings(left)

        # Right: Results
        right = tk.Frame(main, bg=BG)
        right.pack(side="left", fill="both", expand=True)
        self._build_right(right)

        # Bottom: Output table
        self._build_output_table()

    def _build_settings(self, parent):
        tk.Label(parent, text="Settings", font=("Georgia", 13, "bold"),
                 bg=PANEL_BG, fg=DARK).pack(pady=(4, 8))

        tk.Label(parent, text="SELECT ALGORITHM", font=("Helvetica", 8, "bold"),
                 bg=PANEL_BG, fg=DARK).pack(anchor="w", padx=8)

        algo_frame = tk.Frame(parent, bg=WHITE, bd=1, relief="solid")
        algo_frame.pack(fill="x", padx=8, pady=4)

        for algo in ["FCFS", "SJF", "PRIORITY", "SRTF"]:
            btn = tk.Button(algo_frame, text=algo, anchor="w",
                            font=("Helvetica", 9),
                            bg=WHITE, fg=DARK, relief="flat",
                            activebackground=TEAL, activeforeground=WHITE,
                            padx=10, pady=3,
                            command=lambda a=algo: self._select_algo(a))
            btn.pack(fill="x")
            self._style_algo_btn(btn, algo)

        tk.Label(parent, text="NUMBER OF JOBS (N)",
                 font=("Helvetica", 8, "bold"), bg=PANEL_BG, fg=DARK).pack(
                     anchor="w", padx=8, pady=(10, 0))

        n_entry = tk.Entry(parent, textvariable=self.n_var, font=("Helvetica", 10),
                           bg=WHITE, relief="solid", bd=1)
        n_entry.pack(fill="x", padx=8, pady=2)

        btn_row = tk.Frame(parent, bg=PANEL_BG)
        btn_row.pack(fill="x", padx=8, pady=(14, 4))

        tk.Button(btn_row, text="RUN", bg=TEAL, fg=WHITE,
                  font=("Helvetica", 10, "bold"), relief="flat",
                  activebackground=TEAL_DK, activeforeground=WHITE,
                  padx=18, pady=6, cursor="hand2",
                  command=self._run).pack(side="left", padx=(0, 6))

        tk.Button(btn_row, text="CLEAR", bg="#cccccc", fg=DARK,
                  font=("Helvetica", 10), relief="flat",
                  activebackground="#bbb", padx=12, pady=6, cursor="hand2",
                  command=self._clear).pack(side="left")

    def _style_algo_btn(self, btn, algo):
        if self.algorithm_var.get() == algo:
            btn.configure(bg=TEAL, fg=WHITE)
        else:
            btn.configure(bg=WHITE, fg=DARK)
        self._algo_buttons = getattr(self, "_algo_buttons", {})
        self._algo_buttons[algo] = btn

    def _select_algo(self, algo):
        self.algorithm_var.set(algo)
        for a, b in self._algo_buttons.items():
            b.configure(bg=TEAL if a == algo else WHITE,
                        fg=WHITE if a == algo else DARK)

    def _build_right(self, parent):
        res_outer = tk.Frame(parent, bg=PANEL_BG, bd=1, relief="solid")
        res_outer.pack(fill="x")

        tk.Label(res_outer, text="RESULTS SUMMARY",
                 font=("Helvetica", 10, "bold"), bg=PANEL_BG, fg=DARK).pack(
                     anchor="w", padx=12, pady=(8, 4))

        # Stat blocks row
        res_row = tk.Frame(res_outer, bg=PANEL_BG)
        res_row.pack(fill="x", padx=12, pady=(0, 6))

        self.util_lbl  = self._stat_block(res_row, "CPU UTILIZATION",    "–")
        tk.Frame(res_row, bg="#aaa", width=1).pack(side="left", fill="y", padx=10)
        self.turn_lbl  = self._stat_block(res_row, "AVG TURNAROUND",     "–")
        tk.Frame(res_row, bg="#aaa", width=1).pack(side="left", fill="y", padx=10)
        self.wait_lbl  = self._stat_block(res_row, "AVG WAITING",        "–")

        # Separator
        tk.Frame(res_outer, bg="#cccccc", height=1).pack(fill="x", padx=12, pady=(4, 6))

        # Timeline (arrival order)
        tk.Label(res_outer, text="TIMELINE (Arrival Order)",
                 font=("Helvetica", 8, "bold"), bg=PANEL_BG, fg=DARK).pack(
                     anchor="w", padx=12)
        self.arrival_timeline_lbl = tk.Label(res_outer, text="–",
                                     font=("Courier", 10), bg=PANEL_BG, fg=DARK,
                                     anchor="w", wraplength=600, justify="left")
        self.arrival_timeline_lbl.pack(anchor="w", padx=12, pady=(2, 6))

        # Gantt chart (execution order)
        tk.Label(res_outer, text="GANTT CHART (Execution)",
                 font=("Helvetica", 8, "bold"), bg=PANEL_BG, fg=DARK).pack(
                     anchor="w", padx=12)
        self.timeline_lbl = tk.Label(res_outer, text="–",
                                     font=("Courier", 10), bg=PANEL_BG, fg=DARK,
                                     anchor="w", wraplength=600, justify="left")
        self.timeline_lbl.pack(anchor="w", padx=12, pady=(2, 10))

    def _stat_block(self, parent, label, value):
        f = tk.Frame(parent, bg=PANEL_BG)
        f.pack(side="left", padx=10)
        tk.Label(f, text=label, font=("Helvetica", 8, "bold"),
                 bg=PANEL_BG, fg="#555").pack()
        val = tk.Label(f, text=value, font=("Helvetica", 18, "bold"),
                       bg=PANEL_BG, fg=DARK)
        val.pack()
        return val

    # Shared column config: (header text, grid weight, anchor)
    COL_DEFS = [
        ("Job ID",          10, "center"),
        ("Arrival Time",    12, "center"),
        ("Burst Time",      11, "center"),
        ("Priority",        10, "center"),
        ("Turnaround Time", 14, "center"),
        ("Waiting Time",    12, "center"),
        ("",                 6, "center"),
    ]

    def _build_output_table(self):
        outer = tk.Frame(self, bg=BG)
        outer.pack(fill="both", expand=True, padx=20, pady=(4, 12))

        tk.Label(outer, text="OUTPUT VIEW", font=("Helvetica", 10, "bold"),
                 bg=BG, fg=DARK).pack(anchor="w", pady=(0, 4))

        tbl_frame = tk.Frame(outer, bg=BG)
        tbl_frame.pack(fill="x")

        for i, (_, w, _) in enumerate(self.COL_DEFS):
            tbl_frame.columnconfigure(i, weight=w, uniform="tbl")

        for i, (col, _, anchor) in enumerate(self.COL_DEFS):
            tk.Label(tbl_frame, text=col, font=("Helvetica", 9, "bold"),
                     bg=HEADER, fg=WHITE, anchor=anchor,
                     pady=7).grid(row=0, column=i, sticky="nsew", padx=0, pady=0)

        self.rows_frame = tbl_frame
        self._next_row = 1

        btn_area = tk.Frame(outer, bg=BG)
        btn_area.pack(anchor="e", pady=4)
        tk.Button(btn_area, text="Add Job", bg=TEAL, fg=WHITE,
                  font=("Helvetica", 10, "bold"), relief="flat",
                  activebackground=TEAL_DK, padx=14, pady=6, cursor="hand2",
                  command=self._add_job_row).pack()

    # ── Job Rows ────────────────────────────────────────────────────────────────

    def _add_default_jobs(self):
        defaults = [(0, 3, 1), (2, 3, 2), (3, 3, 4), (4, 2, 3)]
        for arr, burst, pri in defaults:
            self._add_job_row(arr, burst, pri)

    def _add_job_row(self, arrival=0, burst=1, priority=1):
        idx = len(self.job_rows)
        pid = f"P{idx+1}"
        row_bg = ROW_EVEN if idx % 2 == 0 else ROW_ALT
        grid_row = self._next_row
        self._next_row += 1

        arr_var = tk.StringVar(value=str(arrival))
        bur_var = tk.StringVar(value=str(burst))
        pri_var = tk.StringVar(value=str(priority))

        f = self.rows_frame

        pid_lbl = tk.Label(f, text=pid, font=("Helvetica", 10, "bold"),
                           bg=row_bg, anchor="center", pady=7)
        pid_lbl.grid(row=grid_row, column=0, sticky="nsew")

        arr_e = tk.Entry(f, textvariable=arr_var, font=("Helvetica", 10),
                         bg=WHITE, relief="solid", bd=1, justify="center")
        arr_e.grid(row=grid_row, column=1, sticky="nsew", padx=4, pady=4)

        bur_e = tk.Entry(f, textvariable=bur_var, font=("Helvetica", 10),
                         bg=WHITE, relief="solid", bd=1, justify="center")
        bur_e.grid(row=grid_row, column=2, sticky="nsew", padx=4, pady=4)

        pri_e = tk.Entry(f, textvariable=pri_var, font=("Helvetica", 10),
                         bg=WHITE, relief="solid", bd=1, justify="center")
        pri_e.grid(row=grid_row, column=3, sticky="nsew", padx=4, pady=4)

        turn_lbl = tk.Label(f, text="–", font=("Helvetica", 10),
                            bg=row_bg, anchor="center")
        turn_lbl.grid(row=grid_row, column=4, sticky="nsew")

        wait_lbl = tk.Label(f, text="–", font=("Helvetica", 10),
                            bg=row_bg, anchor="center")
        wait_lbl.grid(row=grid_row, column=5, sticky="nsew")

        cells = [pid_lbl, arr_e, bur_e, pri_e, turn_lbl, wait_lbl]
        del_btn = tk.Button(f, text="✕", bg=row_bg, fg="#e53935",
                            font=("Helvetica", 10), relief="flat",
                            cursor="hand2",
                            command=lambda gr=grid_row, i=idx, cs=cells: self._delete_row(gr, i, cs))
        del_btn.grid(row=grid_row, column=6, sticky="nsew")
        cells.append(del_btn)

        self.job_rows.append({
            "grid_row": grid_row, "pid": pid,
            "arrival": arr_var, "burst": bur_var, "priority": pri_var,
            "turn_lbl": turn_lbl, "wait_lbl": wait_lbl,
            "cells": cells, "deleted": False
        })

    def _delete_row(self, grid_row, idx, cells):
        for cell in cells:
            cell.grid_remove()
        if idx < len(self.job_rows):
            self.job_rows[idx]["deleted"] = True

    # ── Run Simulation ─────────────────────────────────────────────────────────

    def _get_processes(self):
        procs = []
        for r in self.job_rows:
            if r["deleted"]:
                continue
            try:
                arr = int(r["arrival"].get())
                bur = int(r["burst"].get())
                pri = int(r["priority"].get())
            except ValueError:
                messagebox.showerror("Input Error", f"Invalid input in {r['pid']}")
                return None
            procs.append({"pid": r["pid"], "arrival": arr, "burst": bur, "priority": pri})
        return procs

    def _run(self):
        procs = self._get_processes()
        if not procs:
            return
        if not any(p["burst"] > 0 for p in procs):
            messagebox.showwarning("Warning", "All jobs have 0 burst time.")
            return

        algo = self.algorithm_var.get()
        if algo == "FCFS":
            timeline, results = run_fcfs(procs)
        elif algo == "SJF":
            timeline, results = run_sjf(procs)
        elif algo == "PRIORITY":
            timeline, results = run_priority(procs)
        elif algo == "SRTF":
            timeline, results = run_srtf(procs)
        else:
            return

        self._update_results(procs, results, timeline)
        self._update_table(results)

    def _clear(self):
        for r in self.job_rows:
            if not r["deleted"]:
                r["arrival"].set("0")
                r["burst"].set("1")
                r["priority"].set("1")
                r["turn_lbl"].config(text="–")
                r["wait_lbl"].config(text="–")
        self.util_lbl.config(text="–")
        self.turn_lbl.config(text="–")
        self.wait_lbl.config(text="–")
        self.timeline_lbl.config(text="–")

    # ── Results & Table ────────────────────────────────────────────────────────

    def _build_timeline_text(self, timeline, procs=None):
        """
        Convert timeline segments into a readable execution order string, with queue info.
        If procs is provided, also show which jobs are in the queue at each segment.
        """
        if not timeline:
            return "–"
        # Build a lookup for process info
        proc_info = {p["pid"]: p for p in procs} if procs else {}
        # Gather all jobs
        all_pids = [p["pid"] for p in procs] if procs else []
        parts = []
        for i, seg in enumerate(timeline):
            # Find jobs in the queue at seg['start']
            if procs:
                in_queue = []
                for p in procs:
                    # Not started yet, has arrived
                    started = any(s["pid"] == p["pid"] and s["end"] <= seg["start"] for s in timeline[:i])
                    finished = any(s["pid"] == p["pid"] and s["end"] <= seg["start"] for s in timeline)
                    if p["arrival"] <= seg["start"] and not finished:
                        if p["pid"] != seg["pid"]:
                            in_queue.append(p["pid"])
                queue_str = f"Queue: {', '.join(in_queue) if in_queue else '–'}"
                parts.append(f"[{seg['start']}] {seg['pid']} → [{seg['end']}]  |  {queue_str}")
            else:
                parts.append(f"[{seg['start']}] {seg['pid']} → [{seg['end']}]")
        return "\n".join(parts)

    def _update_results(self, procs, results, timeline):
        if not results:
            return
        valid = [p for p in procs if p["burst"] > 0 and p["pid"] in results]
        if not valid:
            return

        avg_turn = sum(results[p["pid"]]["turnaround"] for p in valid) / len(valid)
        avg_wait = sum(results[p["pid"]]["waiting"] for p in valid) / len(valid)

        max_end  = max(seg["end"] for seg in timeline) if timeline else 1
        busy_time = sum(p["burst"] for p in valid)
        util = round(busy_time / max_end * 100) if max_end > 0 else 0

        self.util_lbl.config(text=f"{util}%")
        self.turn_lbl.config(text=f"{avg_turn:.1f} MS")
        self.wait_lbl.config(text=f"{avg_wait:.1f} MS")

        # Timeline: just arrival order
        arrival_order = sorted(procs, key=lambda p: (p["arrival"], p["pid"]))
        arrival_str = " → ".join(p["pid"] for p in arrival_order)
        self.arrival_timeline_lbl.config(text=arrival_str if arrival_str else "–")

        # Gantt chart: execution order with queue info
        timeline_text = self._build_timeline_text(timeline, procs)
        self.timeline_lbl.config(text=timeline_text)

    def _update_table(self, results):
        for r in self.job_rows:
            if r["deleted"]:
                continue
            pid = r["pid"]
            if pid in results:
                r["turn_lbl"].config(text=f"{results[pid]['turnaround']} ms")
                r["wait_lbl"].config(text=f"{results[pid]['waiting']} ms")


# ─── Entry Point ──────────────────────────────────────────────────────────────

if __name__ == "__main__":
    app = CPUSchedulerApp()
    app.mainloop()