"""
leg_visualize.py
Tek bacagi matplotlib ile cizer. Slider'larla ayak ucunu hareket ettir.
"""

import math
import matplotlib.pyplot as plt
from matplotlib.widgets import Slider

import config
from leg import inverse_kinematics


def draw_leg(ax, x_foot, z_foot):
    ax.clear()
    hip_deg, knee_deg = inverse_kinematics(x_foot, z_foot)

    if hip_deg is None:
        ax.text(0, -100, "ERISILEMEZ\nayak ucu cok uzak veya cok yakin",
                ha="center", va="center", color="red", fontsize=14)
        _setup_axes(ax)
        return

    L1 = config.FEMUR_LENGTH
    L2 = config.TIBIA_LENGTH
    hip_rad = math.radians(hip_deg)
    knee_rad = math.radians(knee_deg)

    hip_pos = (0, 0)
    knee_pos = (L1 * math.cos(hip_rad), L1 * math.sin(hip_rad))
    foot_pos = (knee_pos[0] + L2 * math.cos(hip_rad + knee_rad),
                knee_pos[1] + L2 * math.sin(hip_rad + knee_rad))

    ax.plot([hip_pos[0], knee_pos[0]], [hip_pos[1], knee_pos[1]],
            "b-", linewidth=4, label=f"Femur (L1={L1:.1f}mm)")
    ax.plot([knee_pos[0], foot_pos[0]], [knee_pos[1], foot_pos[1]],
            "r-", linewidth=4, label=f"Tibia (L2={L2:.1f}mm)")
    ax.plot(*hip_pos, "go", markersize=14, label="HIP (sabit)")
    ax.plot(*knee_pos, "ys", markersize=12, label="DIZ pivot")
    ax.plot(*foot_pos, "k^", markersize=14, label="Ayak ucu")
    ax.plot(x_foot, z_foot, "rx", markersize=20, markeredgewidth=3)
    ax.axhline(y=z_foot, color="gray", linestyle="--", alpha=0.3)

    info = (f"Ayak: ({x_foot:+.0f}, {z_foot:+.0f}) mm\n"
            f"Hip:  {hip_deg:+7.2f}\u00b0\n"
            f"Diz:  {knee_deg:+7.2f}\u00b0")
    ax.text(-200, 50, info, fontsize=11, family="monospace",
            bbox=dict(facecolor="lightyellow", edgecolor="black"))

    _setup_axes(ax)


def _setup_axes(ax):
    ax.set_xlim(-220, 220)
    ax.set_ylim(-220, 80)
    ax.set_aspect("equal")
    ax.grid(True, alpha=0.3)
    ax.set_xlabel("X (mm, ileri+)")
    ax.set_ylabel("Z (mm, yukari+)")
    ax.set_title("Tek bacak IK simulatoru")
    ax.legend(loc="upper right", fontsize=9)


if __name__ == "__main__":
    fig, ax = plt.subplots(figsize=(10, 8))
    plt.subplots_adjust(bottom=0.20)

    x_init, z_init = 0, -150
    draw_leg(ax, x_init, z_init)

    ax_x = plt.axes([0.15, 0.10, 0.65, 0.03])
    ax_z = plt.axes([0.15, 0.05, 0.65, 0.03])
    slider_x = Slider(ax_x, "X (mm)", -150, 150, valinit=x_init, valstep=1)
    slider_z = Slider(ax_z, "Z (mm)", -190, -30, valinit=z_init, valstep=1)

    def update(val):
        draw_leg(ax, slider_x.val, slider_z.val)
        fig.canvas.draw_idle()

    slider_x.on_changed(update)
    slider_z.on_changed(update)

    print(">>> Slider'lari kaydirarak ayak ucunu hareket ettir.")
    plt.show()