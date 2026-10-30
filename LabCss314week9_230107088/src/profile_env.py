import argparse, json, os, platform, re, subprocess, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from salt import get_student_params
from paths import RESULTS, STUDENT_ID


def sh(cmd):
    try:
        return subprocess.check_output(cmd, shell=True, text=True,
                                       stderr=subprocess.DEVNULL).strip()
    except Exception:
        return None


def parse_size(s):
    s = s.strip().upper()
    mult = {"K": 1024, "M": 1024**2, "G": 1024**3}
    return int(s[:-1]) * mult[s[-1]] if s[-1] in mult else int(s)


def linux():
    txt = open("/proc/cpuinfo").read()
    model = re.search(r"model name\s*:\s*(.+)", txt)
    mhz = re.search(r"cpu MHz\s*:\s*([\d.]+)", txt)
    caches = {}
    base = "/sys/devices/system/cpu/cpu0/cache"
    try:
        for d in sorted(os.listdir(base)):
            if not d.startswith("index"):
                continue
            rd = lambda f: open(f"{base}/{d}/{f}").read().strip()
            level, typ = rd("level"), rd("type")
            if typ == "Instruction":
                continue
            caches[f"l{level}"] = parse_size(rd("size"))
            caches["line_size"] = int(rd("coherency_line_size"))
    except OSError:
        pass
    out = sh("lscpu -p=CORE,SOCKET")
    physical = len({l for l in out.splitlines() if not l.startswith("#")}) if out else None
    return dict(model=model.group(1) if model else None,
                base_mhz=float(mhz.group(1)) if mhz else None,
                physical_cores=physical, caches=caches)


def macos():
    g = lambda k: sh(f"sysctl -n {k}")
    num = lambda k: int(g(k)) if g(k) else None
    return dict(model=g("machdep.cpu.brand_string"),
                base_mhz=(num("hw.cpufrequency") or 0) / 1e6 or None,
                physical_cores=num("hw.physicalcpu"),
                caches=dict(l1=num("hw.l1dcachesize"), l2=num("hw.l2cachesize"),
                            l3=num("hw.l3cachesize"), line_size=num("hw.cachelinesize")))


def windows():
    ps = ("powershell -NoProfile -Command \"Get-CimInstance Win32_Processor | "
          "Select-Object Name,MaxClockSpeed,NumberOfCores,NumberOfLogicalProcessors,"
          "L2CacheSize,L3CacheSize | ConvertTo-Json\"")
    out = sh(ps)
    d = {}
    if out:
        try:
            d = json.loads(out)
            if isinstance(d, list):
                d = d[0]
        except Exception:
            d = {}
    kb = lambda v: int(v) * 1024 if v else None
    return dict(model=d.get("Name") or platform.processor(),
                base_mhz=d.get("MaxClockSpeed"),
                physical_cores=d.get("NumberOfCores"),
                caches=dict(l1=None,  # not exposed by WMI; fill in from spec sheet
                            l2=kb(d.get("L2CacheSize")),
                            l3=kb(d.get("L3CacheSize")),
                            line_size=64))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--student-id", default=STUDENT_ID)
    args = ap.parse_args()

    if sys.platform.startswith("linux"):
        info = linux()
    elif sys.platform == "darwin":
        info = macos()
    else:
        info = windows()

    logical = os.cpu_count()
    if not info.get("physical_cores"):
        try:
            import psutil
            info["physical_cores"] = psutil.cpu_count(logical=False)
        except ImportError:
            info["physical_cores"] = logical
    if not info["physical_cores"]:
        info["physical_cores"] = logical
    info.update(logical_threads=logical,
                smt_enabled=logical > info["physical_cores"],
                machine=platform.machine(), kernel=platform.release(),
                os=platform.platform(),
                python=dict(impl=platform.python_implementation(),
                            version=platform.python_version()))

    json.dump(info, open(RESULTS / "host_profile.json", "w"), indent=2)
    json.dump(get_student_params(args.student_id),
              open(RESULTS / "salted_params.json", "w"), indent=2)
    print(json.dumps(info, indent=2))


if __name__ == "__main__":
    main()
