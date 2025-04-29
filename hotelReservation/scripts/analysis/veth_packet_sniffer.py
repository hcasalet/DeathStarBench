import subprocess
import time
import re
import threading
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from collections import defaultdict, deque

# === Utility functions ===

def find_veth_interfaces():
    """Find all veth interfaces on the host."""
    interfaces = []
    output = subprocess.check_output(["ip", "-o", "link"], text=True)
    for line in output.splitlines():
        if "veth" in line:
            iface = line.split(":")[1].strip()
            interfaces.append(iface)
    return interfaces

class InterfaceMonitor:
    def __init__(self, iface, duration=60):
        self.iface = iface
        self.duration = duration
        self.retransmissions = 0
        self.timestamps = []
        self.rtts = []
        self.running = True
        self.rtt_window = deque(maxlen=100)  # Sliding window for RTTs

    def monitor(self):
        """Monitor TCP retransmissions and RTTs on an interface."""
        print(f"[*] Monitoring interface {self.iface} for {self.duration}s...")

        try:
            with subprocess.Popen(
                ["tcpdump", "-i", f"{self.iface}", "-nn", "-tt", "--immediate-mode", "tcp"],
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
                text=True,
                bufsize=1,
                shell=True,
            ) as tcpdump_proc:
                print(f"[*] tcpdump started on {self.iface}.")
                retrans_pattern = re.compile(r"Retransmission|Dup Ack")
                ts_pattern = re.compile(r"(\d+\.\d+) IP")
                rtt_pattern = re.compile(r"rtt (\d+\.\d+) ms")

                start_time = time.time()

                while True:
                    line = tcpdump_proc.stdout.readline()
                    if not line:
                        print(tcpdump_proc)
                        print("[!] tcpdump process terminated unexpectedly.")
                        break
                    if not self.running or (time.time() - start_time > self.duration):
                        print(f"[!] Stopping monitoring on {self.iface} after {self.duration}s.")
                        break           

                    if retrans_pattern.search(line):
                        self.retransmissions += 1
                        ts_match = ts_pattern.search(line)
                        if ts_match:
                            timestamp = float(ts_match.group(1))
                            self.timestamps.append(timestamp)
                            print(f"[{time.strftime('%H:%M:%S', time.localtime(timestamp))}] [!] Retransmission or Dup Ack on {self.iface}")

                    # Try extracting RTT if available (tcpdump may show it in some TCP SYN-ACKs)
                    rtt_match = rtt_pattern.search(line)
                    if rtt_match:
                        rtt_ms = float(rtt_match.group(1))
                        self.rtts.append(rtt_ms)
                        self.rtt_window.append(rtt_ms)
            
                tcpdump_proc.terminate()
                print(f"[+] Finished monitoring {self.iface}. Retransmissions: {self.retransmissions}")


        except FileNotFoundError:
            print("[!] tcpdump not found. Install it with `sudo apt install tcpdump`.")
            return

    def stop(self):
        self.running = False

def live_plot(monitors):
    """Live plot retransmission rate and RTT spikes."""
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8))

    def animate(i):
        ax1.clear()
        ax2.clear()

        for monitor in monitors:
            times = [t - monitor.timestamps[0] for t in monitor.timestamps] if monitor.timestamps else []
            retrans_counts = list(range(len(times)))

            ax1.plot(times, retrans_counts, label=f"{monitor.iface} retransmissions")

            if monitor.rtt_window:
                rtts = list(monitor.rtt_window)
                ax2.plot(range(len(rtts)), rtts, label=f"{monitor.iface} RTT (ms)")

        ax1.set_ylabel("Retransmissions")
        ax1.legend()
        ax1.grid(True)

        ax2.set_ylabel("RTT (ms)")
        ax2.set_xlabel("Sample")
        ax2.legend()
        ax2.grid(True)

        fig.tight_layout()

    ani = animation.FuncAnimation(fig, animate, interval=1000)
    plt.show()

def main():
    veths = find_veth_interfaces()
    if not veths:
        print("No veth interfaces found. Are you running containers?")
        return

    print(f"Found veth interfaces: {veths}")

    monitors = []
    threads = []
    monitor_duration = 600  # seconds

    for iface in veths:
        monitor = InterfaceMonitor(iface, duration=monitor_duration)
        monitors.append(monitor)
        t = threading.Thread(target=monitor.monitor)
        t.start()
        threads.append(t)

    # Start live plotting
    # plot_thread = threading.Thread(target=live_plot, args=(monitors,))
    # plot_thread.start()


    for t in threads:
        t.join()
    # for monitor in monitors:
    #     monitor.stop()



if __name__ == "__main__":
    main()
