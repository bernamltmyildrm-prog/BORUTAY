"""
gait_animation.py
Kopek ekranda duz ileri yuruyor: yer sabit, govde X yonunde ilerler.
Bu sayede robotun gercek yuruyus hareketi daha net gorulur.
"""

import math
import matplotlib.pyplot as plt
import matplotlib.animation as animation

import config
from leg import inverse_kinematics
from gait import GaitTrot


# Dizlerin ice kirildigi taraf kopegin onu kabul edildi.
# Bu animasyonda kopegin onu SOL taraftir.
HIP_X_OFFSETS = {
    config.LEG_RF: -config.BODY_LENGTH / 2.0,
    config.LEG_LF: -config.BODY_LENGTH / 2.0,
    config.LEG_RH: +config.BODY_LENGTH / 2.0,
    config.LEG_LH: +config.BODY_LENGTH / 2.0,
}

LEG_STYLE = {
    config.LEG_RF: {"linestyle": "-",  "alpha": 1.0, "label": "RF"},
    config.LEG_RH: {"linestyle": "-",  "alpha": 1.0, "label": "RH"},
    config.LEG_LF: {"linestyle": "--", "alpha": 0.5, "label": "LF"},
    config.LEG_LH: {"linestyle": "--", "alpha": 0.5, "label": "LH"},
}


def compute_leg_geometry(hip_x, foot_x_local, foot_z_local):
    hip_deg, knee_deg = inverse_kinematics(foot_x_local, foot_z_local)

    if hip_deg is None:
        return (hip_x, 0), (hip_x, 0), (hip_x, 0)

    L1 = config.FEMUR_LENGTH
    L2 = config.TIBIA_LENGTH

    hip_rad = math.radians(hip_deg)
    knee_rad = math.radians(knee_deg)

    hip_pos = (hip_x, 0)

    knee_pos = (
        hip_x + L1 * math.cos(hip_rad),
        L1 * math.sin(hip_rad)
    )

    foot_pos = (
        knee_pos[0] + L2 * math.cos(hip_rad + knee_rad),
        knee_pos[1] + L2 * math.sin(hip_rad + knee_rad)
    )

    return hip_pos, knee_pos, foot_pos


# =============================================================================
# ANIMATION SETTINGS
# =============================================================================
GAIT_PERIOD_S = config.GAIT_PERIOD_S
STEP_LENGTH = config.GAIT_STEP_LENGTH_X
FORWARD_VELOCITY_MM_S = STEP_LENGTH / GAIT_PERIOD_S

FPS = 30
DT = 1.0 / FPS

# False: kopek ekranda ileri yurur, yer sabit kalir.
# True: eski mod; kamera kopegi takip eder, govde sabit kalir.
CAMERA_FOLLOW = False

# Kopek ekrani gecince basa sarma mesafesi.
TRACK_LENGTH = 520


# =============================================================================
# FIGURE SETUP
# =============================================================================
fig, ax = plt.subplots(figsize=(13, 7))
gait = GaitTrot()

body_line, = ax.plot([], [], "k-", linewidth=6, label="Govde")

leg_lines = {}

for leg in [config.LEG_RF, config.LEG_RH, config.LEG_LF, config.LEG_LH]:
    style = LEG_STYLE[leg]
    color = "blue" if config.is_front_leg(leg) else "red"

    femur_line, = ax.plot(
        [],
        [],
        color=color,
        linestyle=style["linestyle"],
        alpha=style["alpha"],
        linewidth=3,
        label=f"{style['label']} femur"
    )

    tibia_line, = ax.plot(
        [],
        [],
        color="orange",
        linestyle=style["linestyle"],
        alpha=style["alpha"],
        linewidth=3
    )

    foot_dot, = ax.plot(
        [],
        [],
        "ko",
        alpha=style["alpha"],
        markersize=10
    )

    leg_lines[leg] = (femur_line, tibia_line, foot_dot)


# Zemin cizgisi
ax.axhline(
    y=-config.BODY_STAND_HEIGHT,
    color="brown",
    linestyle="-",
    alpha=0.6,
    linewidth=2
)

# Zemin uzerindeki sabit kisa isaretler
ground_marks = []

for i in range(40):
    line, = ax.plot([], [], color="saddlebrown", linewidth=2, alpha=0.5)
    ground_marks.append(line)


# Hareket yonu oku
ax.annotate(
    "",
    xy=(-220, 50),
    xytext=(-150, 50),
    arrowprops=dict(arrowstyle="->", color="green", lw=3)
)

ax.text(
    -260,
    65,
    "Kopek bu yone yuruyor",
    color="green",
    fontsize=11,
    fontweight="bold"
)


ax.set_xlim(-280, 280)
ax.set_ylim(-200, 90)
ax.set_aspect("equal")
ax.grid(True, alpha=0.2)
ax.set_xlabel("X (mm)")
ax.set_ylabel("Z (mm, yukari+)")
ax.set_title("Quadruped Trot Gait Animation - Straight Walking View")
ax.legend(loc="lower left", fontsize=8, ncol=3)

info_text = ax.text(
    -270,
    60,
    "",
    fontsize=10,
    family="monospace",
    bbox=dict(facecolor="lightyellow", edgecolor="black")
)


# =============================================================================
# ANIMATION LOOP
# =============================================================================
def animate(frame):
    t_global = frame * DT
    t = (t_global / GAIT_PERIOD_S) % 1.0

    # Kopegin onu sol taraf oldugu icin ileri hareket -X yonundedir.
    body_world_x = -FORWARD_VELOCITY_MM_S * t_global

    if CAMERA_FOLLOW:
        body_screen_x = 0.0
    else:
        body_screen_x = (body_world_x % TRACK_LENGTH) - TRACK_LENGTH / 2.0

    # Govde cizimi
    body_line.set_data(
        [
            body_screen_x - config.BODY_LENGTH / 2.0,
            body_screen_x + config.BODY_LENGTH / 2.0
        ],
        [0, 0]
    )

    # Zemin isaretleri
    floor_y = -config.BODY_STAND_HEIGHT
    spacing = 40

    for i, line in enumerate(ground_marks):
        world_marker_x = (i - 20) * spacing

        if CAMERA_FOLLOW:
            screen_x = world_marker_x - (body_world_x % spacing)
        else:
            screen_x = world_marker_x

        if -280 <= screen_x <= 280:
            line.set_data([screen_x, screen_x], [floor_y - 8, floor_y - 2])
        else:
            line.set_data([], [])

    # Bacaklar
    for leg in [config.LEG_RF, config.LEG_RH, config.LEG_LF, config.LEG_LH]:
        foot_x_local, foot_z_local = gait.foot_position(leg, t)

        hip_pos, knee_pos, foot_pos = compute_leg_geometry(
            body_screen_x + HIP_X_OFFSETS[leg],
            foot_x_local,
            foot_z_local
        )

        femur_line, tibia_line, foot_dot = leg_lines[leg]

        femur_line.set_data(
            [hip_pos[0], knee_pos[0]],
            [hip_pos[1], knee_pos[1]]
        )

        tibia_line.set_data(
            [knee_pos[0], foot_pos[0]],
            [knee_pos[1], foot_pos[1]]
        )

        foot_dot.set_data([foot_pos[0]], [foot_pos[1]])

    rf_x, rf_z = gait.foot_position(config.LEG_RF, t)
    in_air = "HAVADA" if rf_z > -config.BODY_STAND_HEIGHT + 0.5 else "YERDE"

    info_text.set_text(
        f"t = {t:.2f}\n"
        f"Govde dunya X: {body_world_x:7.1f} mm\n"
        f"Ekran X:      {body_screen_x:7.1f} mm\n"
        f"Hiz:          {-FORWARD_VELOCITY_MM_S:.1f} mm/s\n"
        f"RF:           {in_air}"
    )

    return ()


anim = animation.FuncAnimation(
    fig,
    animate,
    frames=600,
    interval=int(1000 * DT),
    blit=False,
    repeat=True
)

if CAMERA_FOLLOW:
    print(">>> Kamera takip modu: govde sabit, yer sola kayiyor.")
else:
    print(">>> Dunya modu: yer sabit, kopek ekranda ileri yuruyor.")

plt.show()