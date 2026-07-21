"""
simulator.py
============
Interaktif simulator: kopegi matplotlib ekraninda gor, klavye ile kontrol et.

Guncel yon kabulu:
    - Dizlerin ice kirildigi taraf kopegin onudur.
    - Bu simulator'da kopegin onu SOL taraftir.
    - Bu yuzden ileri yuruyus -X yonundedir.
    - Kopek walk modundayken ekranda sagdan sola dogru ilerler.

main.py ile ayni komut mantigina yakindir, ama ekstra matplotlib penceresi acar
ve kopegi gercek zamanli olarak gosterir.

Klavye komutlari, matplotlib penceresi aktifken:
    SPACE  : stand <-> idle
    w      : walk
    s      : stand
    b      : IMU balance ac/kapat
    +/-    : govde yuksekligi
    [/]    : yuruyus hizi
    q      : cikis

Kullanim:
    python simulator.py
"""

from __future__ import annotations

import math
import matplotlib.pyplot as plt
import matplotlib.animation as animation

import config
from quadruped import QuadRuped
from gyro import GyroProc
from hardware import HardwareController


# =============================================================================
# Kontrol nesnelerini bir kez kur
# =============================================================================
print(">>> Simulator basliyor...")

gyro = GyroProc(use_fake_if_missing=True)
hw = HardwareController(real=False, verbose=False)  # SIM mod, sessiz
dog = QuadRuped(gyro=gyro)
dog.stand()

# Animasyon zaman adimi
DT = config.CONTROL_LOOP_DT
FPS = config.CONTROL_LOOP_HZ

# Yuruyus ekranda gorunsun diye gorsel govde konumu
# Kopegin onu sol oldugu icin ileri hareket -X yonunde olacak.
TRACK_LEFT_X = -190.0
TRACK_RIGHT_X = +190.0
TRACK_LENGTH = TRACK_RIGHT_X - TRACK_LEFT_X
body_visual_distance = 0.0


# =============================================================================
# Bacak konumlari
# =============================================================================
# Guncel gait_animation.py ile ayni konvansiyon:
#   Kopegin onu SOL taraf
#   On bacaklar RF/LF negatif X tarafinda
#   Arka bacaklar RH/LH pozitif X tarafinda
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


# =============================================================================
# Figure + matplotlib elemanlari
# =============================================================================
fig, ax = plt.subplots(figsize=(13, 7))
plt.subplots_adjust(top=0.92, bottom=0.10)

body_line, = ax.plot([], [], "k-", linewidth=6, label="Govde")

leg_lines = {}
for leg in [config.LEG_RF, config.LEG_RH, config.LEG_LF, config.LEG_LH]:
    style = LEG_STYLE[leg]
    color = "blue" if config.is_front_leg(leg) else "red"

    femur_line, = ax.plot(
        [], [],
        color=color,
        linestyle=style["linestyle"],
        alpha=style["alpha"],
        linewidth=3,
        label=f"{style['label']}"
    )

    tibia_line, = ax.plot(
        [], [],
        color="orange",
        linestyle=style["linestyle"],
        alpha=style["alpha"],
        linewidth=3
    )

    foot_dot, = ax.plot(
        [], [],
        "ko",
        alpha=style["alpha"],
        markersize=10
    )

    leg_lines[leg] = (femur_line, tibia_line, foot_dot)


# Zemin cizgisi
ground_line = ax.axhline(
    y=-config.BODY_STAND_HEIGHT,
    color="brown",
    linestyle="-",
    alpha=0.5,
    linewidth=2
)

# Zemin isaretleri sabit kalsin; kopek uzerinden gecsin.
ground_marks = []
for i in range(17):
    x = -320 + i * 40
    line, = ax.plot(
        [x, x],
        [-config.BODY_STAND_HEIGHT - 8, -config.BODY_STAND_HEIGHT - 2],
        color="saddlebrown",
        linewidth=2,
        alpha=0.45
    )
    ground_marks.append(line)


# Hareket yonu oku: ileri = sol
ax.annotate(
    "",
    xy=(-230, 55),
    xytext=(-150, 55),
    arrowprops=dict(arrowstyle="->", color="green", lw=3)
)

ax.text(
    -270, 72,
    "Ileri yon / kopegin onu",
    color="green",
    fontsize=10,
    fontweight="bold"
)

ax.set_xlim(-320, 320)
ax.set_ylim(-230, 105)
ax.set_aspect("equal")
ax.grid(True, alpha=0.2)
ax.set_xlabel("X (mm)  |  ileri yon = -X / sol")
ax.set_ylabel("Z (mm)")
ax.set_title("Quadruped Robot Simulator - Front is LEFT, Forward is -X")
ax.legend(loc="lower left", fontsize=8, ncol=3)

# Sol uste bilgi kutusu
info_text = ax.text(
    -310, 95,
    "",
    fontsize=10,
    family="monospace",
    verticalalignment="top",
    bbox=dict(facecolor="lightyellow", edgecolor="black")
)

# Sag uste komut listesi
help_text = ax.text(
    195, 95,
    ("KOMUTLAR:\n"
     " SPACE: stand/idle\n"
     " w: yuru\n"
     " g: geri yuru\n"
     " s: dur\n"
     " b: balance\n"
     " +/-: yukseklik\n"
     " 1/2: hiz\n"
     " q: cikis"),
    fontsize=9,
    family="monospace",
    verticalalignment="top",
    bbox=dict(facecolor="lavender", edgecolor="black")
)


# =============================================================================
# Klavye olay isleyici
# =============================================================================
def on_key(event):
    """Matplotlib penceresinde klavye tusu basildiginda."""
    raw_key = event.key

    # Debug icin: hangi tus algilandi terminalde gorulsun
    print(f">>> KEY pressed: {repr(raw_key)}")

    if raw_key is None:
        return

    # ONEMLI:
    # SPACE tusu bazen ' ', bazen 'space' gelir.
    # Bu yuzden once SPACE kontrolu yapilir.
    # str(...).strip() SPACE'i bos stringe cevirdigi icin space bozuluyordu.
    if raw_key == " " or raw_key == "space":
        if dog.mode == dog.MODE_STAND:
            dog.idle()
            print(">>> mode: IDLE / CROUCH")
        else:
            dog.stand()
            print(">>> mode: STAND")
        return

    # Space disindaki tuslar icin normalize et
    key = str(raw_key).lower()

    # ileri
    if key in ["w", "up"]:
        dog.walk_forward(speed_scale=dog.speed_scale)
        print(">>> mode: WALK FORWARD")
        return

    # geri
    if key in ["g", "down"]:
        dog.walk_backward(speed_scale=dog.speed_scale)
        print(">>> mode: WALK BACKWARD")
        return

    # stand
    if key == "s":
        dog.stand()
        print(">>> mode: STAND")
        return

    # crouch
    if key == "c":
        dog.idle()
        print(">>> mode: CROUCH / IDLE")
        return

    # balance
    if key == "b":
        new_state = not dog.balance_enabled
        dog.enable_balance(new_state)
        print(f">>> balance: {'ACIK' if new_state else 'KAPALI'}")
        return

    # height up
    if key in ["+", "="]:
        dog.set_body_height(dog.body_height + 5.0)
        print(f">>> height: {dog.body_height:.1f} mm")
        return

    # height down
    if key in ["-", "_"]:
        dog.set_body_height(dog.body_height - 5.0)
        print(f">>> height: {dog.body_height:.1f} mm")
        return

    # speed down
    if key == "1":
        dog.speed_scale = max(0.3, dog.speed_scale - 0.1)
        print(f">>> speed: {dog.speed_scale:.2f}")
        return

    # speed up
    if key == "2":
        dog.speed_scale = min(1.2, dog.speed_scale + 0.1)
        print(f">>> speed: {dog.speed_scale:.2f}")
        return

    # quit
    if key in ["q", "escape"]:
        plt.close(fig)
        return


fig.canvas.mpl_connect("key_press_event", on_key)


# =============================================================================
# Yardimci fonksiyonlar
# =============================================================================
def compute_body_screen_x():
    """
    Forward modda köpek sola gider.
    Backward modda köpek sağa gider.
    """
    global body_visual_distance

    if dog.mode == dog.MODE_WALK:
        forward_speed_mm_s = config.GAIT_STEP_LENGTH_X / max(config.GAIT_PERIOD_S, 1e-6)

        direction_sign = getattr(dog, "walk_direction", +1.0)

        # walk_direction +1 ise ileri: sola doğru gitmeli.
        # walk_direction -1 ise geri: sağa doğru gitmeli.
        body_visual_distance += forward_speed_mm_s * dog.speed_scale * DT * direction_sign

    wrapped = body_visual_distance % TRACK_LENGTH
    return TRACK_RIGHT_X - wrapped


def update_ground_marks():
    """Zemin cizgilerini mevcut govde yuksekligine gore gunceller."""
    floor_y = -dog.body_height

    for i, line in enumerate(ground_marks):
        x = -320 + i * 40
        line.set_data([x, x], [floor_y - 8, floor_y - 2])


# =============================================================================
# Animasyon dongusu
# =============================================================================
def animate(frame):
    # 1) Bir kontrol adimi calistir
    targets = dog.update(dt=DT)
    hw.apply_targets(targets)  # SIM modunda sessiz

    # 2) Govde ekran konumu
    body_screen_x = compute_body_screen_x()

    body_line.set_data(
        [
            body_screen_x - config.BODY_LENGTH / 2.0,
            body_screen_x + config.BODY_LENGTH / 2.0
        ],
        [0, 0]
    )

    # 3) Bacaklari ciz
    L1 = config.FEMUR_LENGTH
    L2 = config.TIBIA_LENGTH

    for leg in [config.LEG_RF, config.LEG_RH, config.LEG_LF, config.LEG_LH]:
        target = targets[leg]

        femur_line, tibia_line, foot_dot = leg_lines[leg]

        if not target.reachable or target.hip_deg is None or target.knee_deg is None:
            femur_line.set_data([], [])
            tibia_line.set_data([], [])
            foot_dot.set_data([], [])
            continue

        hip_x = body_screen_x + HIP_X_OFFSETS[leg]

        hip_rad = math.radians(target.hip_deg)
        knee_rad = math.radians(target.knee_deg)

        # Eklem pozisyonlari, yandan gorunum, X-Z duzlemi
        hip_pos = (hip_x, 0)

        knee_pos = (
            hip_x + L1 * math.cos(hip_rad),
            L1 * math.sin(hip_rad)
        )

        foot_pos = (
            knee_pos[0] + L2 * math.cos(hip_rad + knee_rad),
            knee_pos[1] + L2 * math.sin(hip_rad + knee_rad)
        )

        femur_line.set_data(
            [hip_pos[0], knee_pos[0]],
            [hip_pos[1], knee_pos[1]]
        )

        tibia_line.set_data(
            [knee_pos[0], foot_pos[0]],
            [knee_pos[1], foot_pos[1]]
        )

        foot_dot.set_data([foot_pos[0]], [foot_pos[1]])

    # 4) Zemin yuksekligini govde yuksekligine gore guncelle
    ground_line.set_ydata([-dog.body_height, -dog.body_height])
    update_ground_marks()

    # 5) Bilgi kutusu
    balance_txt = "ON" if dog.balance_enabled else "OFF"

    imu_line = ""
    if dog.imu_state is not None:
        imu_line = (
            f"\nIMU roll : {dog.imu_state.roll_deg:+6.2f} deg"
            f"\nIMU pitch: {dog.imu_state.pitch_deg:+6.2f} deg"
            f"\npitch corr: {dog.last_pitch_correction_mm:+6.2f} mm"
        )

    info_text.set_text(
        f"Mode    : {dog.mode}\n"
        f"Phase   : {dog.phase:.2f}\n"
        f"Height  : {dog.body_height:.1f} mm\n"
        f"Speed   : {dog.speed_scale:.2f}\n"
        f"Body X  : {body_screen_x:+.1f} mm\n"
        f"Balance : {balance_txt}"
        f"{imu_line}"
    )

    return ()


anim = animation.FuncAnimation(
    fig,
    animate,
    interval=int(1000 * DT),
    blit=False,
    repeat=True,
    cache_frame_data=False,
)


# =============================================================================
# Ana program
# =============================================================================
if __name__ == "__main__":
    print()
    print("=" * 60)
    print("QUADRUPED SIMULATOR")
    print("=" * 60)
    print("  Matplotlib penceresine TIKLA, sonra tuslara bas:")
    print("    SPACE  : stand <-> idle")
    print("    w      : ileri yuru")
    print("    g      : geri yuru")
    print("    s      : stand")
    print("    b      : IMU balance toggle")
    print("    +/-    : govde yukseklik")
    print("    1/2    : yuruyus hizi")
    print("    q      : cikis")
    print()
    print("  Guncel yon:")
    print("    Kopegin onu SOL taraf")
    print("    Ileri hareket -X yonu")
    print("=" * 60)
    print()

    try:
        plt.show()
    finally:
        gyro.close()
        print(">>> Simulator kapatildi.")
