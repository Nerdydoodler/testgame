import math
import random
import sys

import pygame


WIDTH = 800
HEIGHT = 600
FPS = 60

PLAYER_SPEED = 280.0
PLAYER_SLOW_MULT = 0.45
PLAYER_RADIUS = 10

PLAYER_BULLET_SPEED = 520.0
PLAYER_BULLET_RADIUS = 4
PLAYER_SHOT_COOLDOWN = 0.09

SUPER_BULLET_SPEED = 420.0
SUPER_BULLET_RADIUS = 18

ENEMY_RADIUS = 18
ENEMY_BULLET_SPEED = 220.0
ENEMY_BULLET_RADIUS = 5

MAX_HP = 20
SUPER_DAMAGE = 20
SUPER_COOLDOWN = 3.0

BOSS_HP_GROWTH = 1.35

DIFFICULTIES = {
    "easy": {"boss_hp": 50, "heal_interval": 5.0},
    "normal": {"boss_hp": 100, "heal_interval": 10.0},
    "hard": {"boss_hp": 200, "heal_interval": 30.0},
}
DIFFICULTY_ORDER = ["easy", "normal", "hard"]
DEFAULT_DIFFICULTY = "normal"

HEAL_AMOUNT = 5
HEAL_FALL_SPEED = 70.0
HEAL_RADIUS = 12

COLOR_PALETTE = [
    (120, 255, 140),
    (110, 200, 255),
    (255, 220, 120),
    (255, 140, 220),
    (220, 80, 80),
    (180, 180, 255),
    (235, 235, 235),
]


def clamp(v, lo, hi):
    return lo if v < lo else hi if v > hi else v


def dist2(ax, ay, bx, by):
    dx = ax - bx
    dy = ay - by
    return dx * dx + dy * dy


class Player:
    def __init__(self):
        self.x = WIDTH * 0.5
        self.y = HEIGHT * 0.82

        self.move_speed = PLAYER_SPEED
        self.bullet_damage = 1
        self.super_damage = SUPER_DAMAGE
        self.super_cooldown = SUPER_COOLDOWN
        self.max_hp = MAX_HP

        self.hp = self.max_hp
        self.shot_cd = 0.0
        self.super_cd = 0.0

    def reset_position(self):
        self.x = WIDTH * 0.5
        self.y = HEIGHT * 0.82

    def reset_run_stats(self):
        self.move_speed = PLAYER_SPEED
        self.bullet_damage = 1
        self.super_damage = SUPER_DAMAGE
        self.super_cooldown = SUPER_COOLDOWN
        self.max_hp = MAX_HP
        self.hp = self.max_hp
        self.shot_cd = 0.0
        self.super_cd = 0.0

    def reset_for_new_run(self):
        self.reset_position()
        self.reset_run_stats()

    def update(self, dt, keys):
        speed = self.move_speed
        if keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT]:
            speed *= PLAYER_SLOW_MULT

        dx = 0.0
        dy = 0.0
        if keys[pygame.K_a] or keys[pygame.K_LEFT]:
            dx -= 1.0
        if keys[pygame.K_d] or keys[pygame.K_RIGHT]:
            dx += 1.0
        if keys[pygame.K_w] or keys[pygame.K_UP]:
            dy -= 1.0
        if keys[pygame.K_s] or keys[pygame.K_DOWN]:
            dy += 1.0

        if dx != 0.0 or dy != 0.0:
            inv = 1.0 / math.sqrt(dx * dx + dy * dy)
            dx *= inv
            dy *= inv

        self.x += dx * speed * dt
        self.y += dy * speed * dt

        pad = PLAYER_RADIUS + 6
        self.x = clamp(self.x, pad, WIDTH - pad)
        self.y = clamp(self.y, pad, HEIGHT - pad)

        self.shot_cd = max(0.0, self.shot_cd - dt)
        self.super_cd = max(0.0, self.super_cd - dt)

    def can_shoot(self):
        return self.shot_cd <= 0.0

    def shoot(self):
        self.shot_cd = PLAYER_SHOT_COOLDOWN

    def can_super(self):
        return self.super_cd <= 0.0

    def use_super(self):
        self.super_cd = self.super_cooldown


class Enemy:
    def __init__(self):
        self.x = WIDTH * 0.5
        self.y = HEIGHT * 0.22
        self.t = 0.0
        self.base_x = self.x

    def reset(self):
        self.x = WIDTH * 0.5
        self.y = HEIGHT * 0.22
        self.t = 0.0
        self.base_x = self.x

    def update(self, dt):
        self.t += dt
        self.x = self.base_x + math.sin(self.t * 0.9) * 220.0


class Bullet:
    def __init__(self, x, y, vx, vy, radius, friendly, damage=1):
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.radius = radius
        self.friendly = friendly
        self.damage = damage
        self.dead = False

    def update(self, dt):
        self.x += self.vx * dt
        self.y += self.vy * dt
        if (
            self.x < -40
            or self.x > WIDTH + 40
            or self.y < -60
            or self.y > HEIGHT + 60
        ):
            self.dead = True


class HealPickup:
    def __init__(self, x):
        self.x = x
        self.y = -24
        self.vy = HEAL_FALL_SPEED
        self.radius = HEAL_RADIUS
        self.dead = False

    def update(self, dt):
        self.y += self.vy * dt
        if self.y > HEIGHT + 40:
            self.dead = True


def spawn_player_bullets(player, bullets):
    bullets.append(
        Bullet(
            player.x,
            player.y - 12,
            0.0,
            -PLAYER_BULLET_SPEED,
            PLAYER_BULLET_RADIUS,
            True,
            player.bullet_damage,
        )
    )


def spawn_heal_pickup(pickups):
    x = random.uniform(24, WIDTH - 24)
    pickups.append(HealPickup(x))


def draw_heal_pickup(surface, p):
    x = int(p.x)
    y = int(p.y)
    s = 7
    w = 4
    green = (80, 230, 110)
    pygame.draw.rect(surface, green, (x - w // 2, y - s, w, 2 * s), border_radius=2)
    pygame.draw.rect(surface, green, (x - s, y - w // 2, 2 * s, w), border_radius=2)


def spawn_super_bullet(player, bullets):
    bullets.append(
        Bullet(
            player.x,
            player.y - 18,
            0.0,
            -SUPER_BULLET_SPEED,
            SUPER_BULLET_RADIUS,
            True,
            player.super_damage,
        )
    )


def pattern_ring_burst(enemy, player, bullets, t_global, dt, level):
    ring_period = max(0.95, 1.25 - level * 0.03)
    if int(t_global / ring_period) != int((t_global - dt) / ring_period):
        n = int(clamp(18 + level * 2, 18, 44))
        base = t_global * 1.6
        spd = ENEMY_BULLET_SPEED * (1.0 + 0.03 * level)
        for i in range(n):
            ang = base + (i / n) * math.tau
            vx = math.cos(ang) * spd
            vy = math.sin(ang) * spd
            bullets.append(Bullet(enemy.x, enemy.y, vx, vy, ENEMY_BULLET_RADIUS, False, 1))


def pattern_aimed_spread(enemy, player, bullets, t_global, dt, level):
    aimed_period = max(0.22, 0.42 - level * 0.01)
    if int(t_global / aimed_period) != int((t_global - dt) / aimed_period):
        dx = player.x - enemy.x
        dy = player.y - enemy.y
        d = math.hypot(dx, dy)
        if d > 0.001:
            dx /= d
            dy /= d
        spread = 0.20
        spd = ENEMY_BULLET_SPEED * (1.10 + 0.02 * level)
        for s in (-spread, 0.0, spread):
            ang = math.atan2(dy, dx) + s
            vx = math.cos(ang) * spd
            vy = math.sin(ang) * spd
            bullets.append(Bullet(enemy.x, enemy.y, vx, vy, ENEMY_BULLET_RADIUS, False, 1))


def pattern_spiral_stream(enemy, player, bullets, t_global, dt, level):
    step_period = max(0.05, 0.09 - level * 0.002)
    if int(t_global / step_period) != int((t_global - dt) / step_period):
        ang = t_global * (2.2 + level * 0.12)
        spd = ENEMY_BULLET_SPEED * (0.95 + 0.02 * level)
        vx = math.cos(ang) * spd
        vy = math.sin(ang) * spd
        bullets.append(Bullet(enemy.x, enemy.y, vx, vy, ENEMY_BULLET_RADIUS, False, 1))


def pattern_downward_rain(enemy, player, bullets, t_global, dt, level):
    rain_period = max(0.10, 0.18 - level * 0.003)
    if int(t_global / rain_period) != int((t_global - dt) / rain_period):
        count = int(clamp(1 + level // 3, 1, 4))
        for _ in range(count):
            ang = math.pi * 0.5 + random.uniform(-0.55, 0.55)
            spd = ENEMY_BULLET_SPEED * (0.95 + 0.02 * level)
            vx = math.cos(ang) * spd
            vy = math.sin(ang) * spd
            bullets.append(Bullet(enemy.x, enemy.y, vx, vy, ENEMY_BULLET_RADIUS, False, 1))


PATTERN_POOL = [
    ("Ring Burst", pattern_ring_burst),
    ("Aimed Spread", pattern_aimed_spread),
    ("Spiral Stream", pattern_spiral_stream),
    ("Downward Rain", pattern_downward_rain),
]


def choose_patterns(level):
    n = int(clamp(1 + level // 2, 1, len(PATTERN_POOL)))
    return random.sample(PATTERN_POOL, n)


def spawn_enemy_patterns(enemy, player, bullets, t_global, dt, level, patterns):
    for _, fn in patterns:
        fn(enemy, player, bullets, t_global, dt, level)


def draw_text_center(surface, font, text, y, color):
    img = font.render(text, True, color)
    rect = img.get_rect(center=(WIDTH // 2, int(y)))
    surface.blit(img, rect)


def draw_button(surface, font, rect, text, enabled=True):
    mouse_pos = pygame.mouse.get_pos()
    hovered = rect.collidepoint(mouse_pos)
    if not enabled:
        bg = (45, 45, 55)
        fg = (150, 150, 160)
        border = (80, 80, 95)
    else:
        bg = (55, 55, 70) if not hovered else (75, 75, 95)
        fg = (235, 235, 235)
        border = (120, 120, 140)

    pygame.draw.rect(surface, bg, rect, border_radius=10)
    pygame.draw.rect(surface, border, rect, width=2, border_radius=10)
    img = font.render(text, True, fg)
    surface.blit(img, img.get_rect(center=rect.center))
    return hovered


UPGRADE_POOL = [
    ("speed", "Speed Up", "+40 move speed"),
    ("damage", "Damage Up", "+1 bullet damage"),
    ("super_damage", "Super Damage", "+10 super damage"),
    ("super_cd", "Super Cooldown", "-0.4s super cooldown"),
    ("health", "Max Health", "+5 max HP"),
]


def roll_upgrades():
    return random.sample(UPGRADE_POOL, 3)


def apply_upgrade(player, upgrade_id):
    if upgrade_id == "speed":
        player.move_speed += 40.0
    elif upgrade_id == "damage":
        player.bullet_damage += 1
    elif upgrade_id == "super_damage":
        player.super_damage += 10
    elif upgrade_id == "super_cd":
        player.super_cooldown = max(0.6, player.super_cooldown - 0.4)
    elif upgrade_id == "health":
        player.max_hp += 5
        player.hp = min(player.max_hp, player.hp + 5)


def boss_hp_for_level(base_boss_hp, level):
    return int(round(base_boss_hp * (BOSS_HP_GROWTH ** (level - 1))))


def reset_run(player, enemy, base_boss_hp, heal_interval):
    player.reset_for_new_run()
    enemy.reset()
    level = 1
    boss_max_hp = boss_hp_for_level(base_boss_hp, level)
    boss_hp = boss_max_hp
    patterns = choose_patterns(level)
    return [], [], [], 0.0, level, boss_hp, boss_max_hp, heal_interval, heal_interval, patterns


def start_next_level(player, enemy, base_boss_hp, heal_interval, level):
    player.reset_position()
    enemy.reset()
    boss_max_hp = boss_hp_for_level(base_boss_hp, level)
    boss_hp = boss_max_hp
    patterns = choose_patterns(level)
    return [], [], [], 0.0, boss_hp, boss_max_hp, heal_interval, patterns


def main():
    pygame.init()
    pygame.display.set_caption("Bullet Hell")
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    clock = pygame.time.Clock()

    font = pygame.font.SysFont(None, 28)
    big_font = pygame.font.SysFont(None, 72)
    menu_font = pygame.font.SysFont(None, 44)

    player = Player()
    enemy = Enemy()

    player_bullets = []
    enemy_bullets = []
    heal_pickups = []
    t_global = 0.0
    difficulty = DEFAULT_DIFFICULTY
    base_boss_hp = DIFFICULTIES[difficulty]["boss_hp"]
    heal_interval = DIFFICULTIES[difficulty]["heal_interval"]
    heal_spawn_timer = heal_interval
    level = 1
    boss_max_hp = boss_hp_for_level(base_boss_hp, level)
    boss_hp = boss_max_hp
    patterns = choose_patterns(level)

    upgrade_choices = []

    player_color_idx = 0
    enemy_color_idx = 4
    player_color = COLOR_PALETTE[player_color_idx]
    enemy_color = COLOR_PALETTE[enemy_color_idx]

    state = "menu"

    running = True
    while running:
        dt = clock.tick(FPS) / 1000.0
        dt = min(dt, 1.0 / 20.0)

        play_rect = pygame.Rect(WIDTH // 2 - 140, int(HEIGHT * 0.46), 280, 56)
        options_rect = pygame.Rect(WIDTH // 2 - 140, int(HEIGHT * 0.56), 280, 56)
        quit_rect = pygame.Rect(WIDTH // 2 - 140, int(HEIGHT * 0.66), 280, 56)

        opt_back_rect = pygame.Rect(18, 18, 120, 44)
        p_left = pygame.Rect(WIDTH // 2 + 40, int(HEIGHT * 0.36), 46, 46)
        p_right = pygame.Rect(WIDTH // 2 + 200, int(HEIGHT * 0.36), 46, 46)
        e_left = pygame.Rect(WIDTH // 2 + 40, int(HEIGHT * 0.48), 46, 46)
        e_right = pygame.Rect(WIDTH // 2 + 200, int(HEIGHT * 0.48), 46, 46)
        p_swatch = pygame.Rect(WIDTH // 2 + 100, int(HEIGHT * 0.36), 90, 46)
        e_swatch = pygame.Rect(WIDTH // 2 + 100, int(HEIGHT * 0.48), 90, 46)

        diff_easy = pygame.Rect(WIDTH // 2 - 200, int(HEIGHT * 0.62), 120, 50)
        diff_normal = pygame.Rect(WIDTH // 2 - 60, int(HEIGHT * 0.62), 120, 50)
        diff_hard = pygame.Rect(WIDTH // 2 + 80, int(HEIGHT * 0.62), 120, 50)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    if state in ("upgrade",):
                        state = "menu"
                    else:
                        running = False
                if event.key == pygame.K_p and state in ("playing", "paused"):
                    state = "paused" if state == "playing" else "playing"
                if event.key == pygame.K_x and state == "playing":
                    if boss_hp > 0 and player.can_super():
                        spawn_super_bullet(player, player_bullets)
                        player.use_super()
                if state == "upgrade" and event.key in (pygame.K_1, pygame.K_2, pygame.K_3):
                    idx = event.key - pygame.K_1
                    if 0 <= idx < len(upgrade_choices):
                        apply_upgrade(player, upgrade_choices[idx][0])
                        level += 1
                        (
                            player_bullets,
                            enemy_bullets,
                            heal_pickups,
                            t_global,
                            boss_hp,
                            boss_max_hp,
                            heal_spawn_timer,
                            patterns,
                        ) = start_next_level(player, enemy, base_boss_hp, heal_interval, level)
                        state = "playing"
                if state == "game_over" and event.key == pygame.K_r:
                    (
                        player_bullets,
                        enemy_bullets,
                        heal_pickups,
                        t_global,
                        level,
                        boss_hp,
                        boss_max_hp,
                        heal_interval,
                        heal_spawn_timer,
                        patterns,
                    ) = reset_run(player, enemy, base_boss_hp, heal_interval)
                    state = "playing"
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mx, my = event.pos
                if state == "menu":
                    if play_rect.collidepoint(mx, my):
                        (
                            player_bullets,
                            enemy_bullets,
                            heal_pickups,
                            t_global,
                            level,
                            boss_hp,
                            boss_max_hp,
                            heal_interval,
                            heal_spawn_timer,
                            patterns,
                        ) = reset_run(player, enemy, base_boss_hp, heal_interval)
                        state = "playing"
                    elif options_rect.collidepoint(mx, my):
                        state = "options"
                    elif quit_rect.collidepoint(mx, my):
                        running = False
                elif state == "options":
                    if opt_back_rect.collidepoint(mx, my):
                        state = "menu"
                    elif p_left.collidepoint(mx, my):
                        player_color_idx = (player_color_idx - 1) % len(COLOR_PALETTE)
                        player_color = COLOR_PALETTE[player_color_idx]
                    elif p_right.collidepoint(mx, my):
                        player_color_idx = (player_color_idx + 1) % len(COLOR_PALETTE)
                        player_color = COLOR_PALETTE[player_color_idx]
                    elif e_left.collidepoint(mx, my):
                        enemy_color_idx = (enemy_color_idx - 1) % len(COLOR_PALETTE)
                        enemy_color = COLOR_PALETTE[enemy_color_idx]
                    elif e_right.collidepoint(mx, my):
                        enemy_color_idx = (enemy_color_idx + 1) % len(COLOR_PALETTE)
                        enemy_color = COLOR_PALETTE[enemy_color_idx]
                    elif diff_easy.collidepoint(mx, my):
                        difficulty = "easy"
                    elif diff_normal.collidepoint(mx, my):
                        difficulty = "normal"
                    elif diff_hard.collidepoint(mx, my):
                        difficulty = "hard"

                    boss_max_hp = DIFFICULTIES[difficulty]["boss_hp"]
                    heal_interval = DIFFICULTIES[difficulty]["heal_interval"]
                    base_boss_hp = DIFFICULTIES[difficulty]["boss_hp"]

                elif state == "upgrade":
                    up_rects = [
                        pygame.Rect(WIDTH // 2 - 240, int(HEIGHT * 0.42), 480, 56),
                        pygame.Rect(WIDTH // 2 - 240, int(HEIGHT * 0.52), 480, 56),
                        pygame.Rect(WIDTH // 2 - 240, int(HEIGHT * 0.62), 480, 56),
                    ]
                    for i, r in enumerate(up_rects):
                        if r.collidepoint(mx, my) and i < len(upgrade_choices):
                            apply_upgrade(player, upgrade_choices[i][0])
                            level += 1
                            (
                                player_bullets,
                                enemy_bullets,
                                heal_pickups,
                                t_global,
                                boss_hp,
                                boss_max_hp,
                                heal_spawn_timer,
                                patterns,
                            ) = start_next_level(player, enemy, base_boss_hp, heal_interval, level)
                            state = "playing"
                            break

        keys = pygame.key.get_pressed()

        if state == "playing":
            t_global += dt
            player.update(dt, keys)
            enemy.update(dt)

            heal_spawn_timer -= dt
            if heal_spawn_timer <= 0.0:
                spawn_heal_pickup(heal_pickups)
                heal_spawn_timer = heal_interval

            if (keys[pygame.K_z] or keys[pygame.K_SPACE]) and player.can_shoot():
                player.shoot()
                spawn_player_bullets(player, player_bullets)

            if boss_hp > 0:
                spawn_enemy_patterns(enemy, player, enemy_bullets, t_global, dt, level, patterns)

            for b in player_bullets:
                b.update(dt)
                if not b.dead:
                    if dist2(b.x, b.y, enemy.x, enemy.y) <= (b.radius + ENEMY_RADIUS) ** 2:
                        b.dead = True
                        boss_hp = max(0, boss_hp - b.damage)

            for b in enemy_bullets:
                b.update(dt)
                if not b.dead:
                    if dist2(b.x, b.y, player.x, player.y) <= (b.radius + PLAYER_RADIUS) ** 2:
                        b.dead = True
                        player.hp = max(0, player.hp - 1)

            for p in heal_pickups:
                p.update(dt)
                if not p.dead:
                    if dist2(p.x, p.y, player.x, player.y) <= (p.radius + PLAYER_RADIUS) ** 2:
                        p.dead = True
                        player.hp = min(player.max_hp, player.hp + HEAL_AMOUNT)

            player_bullets = [b for b in player_bullets if not b.dead]
            enemy_bullets = [b for b in enemy_bullets if not b.dead]
            heal_pickups = [p for p in heal_pickups if not p.dead]

            if boss_hp <= 0:
                state = "upgrade"
                upgrade_choices = roll_upgrades()
                enemy_bullets = []
                heal_pickups = []

            if player.hp <= 0:
                state = "game_over"

        screen.fill((10, 10, 14))

        if state == "menu":
            draw_text_center(screen, big_font, "BULLET HELL", HEIGHT * 0.26, (235, 235, 235))
            draw_text_center(screen, font, "Z/Space: Shoot   X: Super   P: Pause", HEIGHT * 0.34, (200, 200, 210))
            draw_button(screen, menu_font, play_rect, "PLAY")
            draw_button(screen, menu_font, options_rect, "OPTIONS")
            draw_button(screen, menu_font, quit_rect, "QUIT")
            pygame.display.flip()
            continue

        if state == "options":
            draw_text_center(screen, big_font, "OPTIONS", HEIGHT * 0.20, (235, 235, 235))

            draw_button(screen, font, opt_back_rect, "BACK")

            player_label = font.render("Player Color", True, (235, 235, 235))
            screen.blit(player_label, (WIDTH // 2 - 200, int(HEIGHT * 0.36) + 12))
            draw_button(screen, font, p_left, "<")
            pygame.draw.rect(screen, player_color, p_swatch, border_radius=8)
            pygame.draw.rect(screen, (140, 140, 160), p_swatch, width=2, border_radius=8)
            draw_button(screen, font, p_right, ">")

            enemy_label = font.render("Enemy Color", True, (235, 235, 235))
            screen.blit(enemy_label, (WIDTH // 2 - 200, int(HEIGHT * 0.48) + 12))
            draw_button(screen, font, e_left, "<")
            pygame.draw.rect(screen, enemy_color, e_swatch, border_radius=8)
            pygame.draw.rect(screen, (140, 140, 160), e_swatch, width=2, border_radius=8)
            draw_button(screen, font, e_right, ">")

            diff_label = font.render("Difficulty", True, (235, 235, 235))
            screen.blit(diff_label, (WIDTH // 2 - 200, int(HEIGHT * 0.62) + 14))

            draw_button(screen, font, diff_easy, "EASY", enabled=True)
            draw_button(screen, font, diff_normal, "NORMAL", enabled=True)
            draw_button(screen, font, diff_hard, "HARD", enabled=True)

            sel_rect = {"easy": diff_easy, "normal": diff_normal, "hard": diff_hard}[difficulty]
            pygame.draw.rect(screen, (90, 220, 120), sel_rect, width=4, border_radius=10)

            hint = font.render(
                f"Boss HP: {DIFFICULTIES[difficulty]['boss_hp']}   Heal every ~{DIFFICULTIES[difficulty]['heal_interval']:.0f}s",
                True,
                (200, 200, 210),
            )
            screen.blit(hint, (WIDTH // 2 - 200, int(HEIGHT * 0.72)))

            pygame.display.flip()
            continue

        pygame.draw.circle(screen, enemy_color, (int(enemy.x), int(enemy.y)), ENEMY_RADIUS)

        for b in player_bullets:
            if b.damage >= SUPER_DAMAGE:
                pygame.draw.circle(screen, (60, 150, 255), (int(b.x), int(b.y)), b.radius)
            else:
                pygame.draw.circle(screen, (110, 200, 255), (int(b.x), int(b.y)), b.radius)

        for b in enemy_bullets:
            pygame.draw.circle(screen, (255, 200, 90), (int(b.x), int(b.y)), b.radius)

        for p in heal_pickups:
            draw_heal_pickup(screen, p)

        px = int(player.x)
        py = int(player.y)
        pygame.draw.polygon(
            screen,
            player_color,
            [(px, py - 14), (px - 10, py + 12), (px + 10, py + 12)],
        )
        pygame.draw.circle(screen, (40, 40, 40), (px, py), 3)

        hp_text = font.render(f"HP: {player.hp}/{player.max_hp}", True, (235, 235, 235))
        screen.blit(hp_text, (16, 14))

        lvl_text = font.render(f"Level: {level}", True, (235, 235, 235))
        screen.blit(lvl_text, (16, 86))

        bar_x = 16
        bar_y = 42
        bar_w = 220
        bar_h = 12
        pygame.draw.rect(screen, (30, 30, 40), (bar_x, bar_y, bar_w, bar_h), border_radius=3)
        fill_w = int(bar_w * (player.hp / player.max_hp)) if player.max_hp > 0 else 0
        pygame.draw.rect(screen, (90, 220, 120), (bar_x, bar_y, fill_w, bar_h), border_radius=3)

        if player.super_cd <= 0.0 and state == "playing":
            super_text = font.render("SUPER (X): READY", True, (235, 235, 235))
            screen.blit(super_text, (16, 62))

        boss_bar_x = 16
        boss_bar_w = WIDTH - 32
        boss_bar_h = 22
        boss_bar_y = HEIGHT - 16 - boss_bar_h
        pygame.draw.rect(
            screen,
            (35, 18, 18),
            (boss_bar_x, boss_bar_y, boss_bar_w, boss_bar_h),
            border_radius=6,
        )
        boss_fill_w = int(boss_bar_w * (boss_hp / boss_max_hp)) if boss_max_hp > 0 else 0
        pygame.draw.rect(
            screen,
            (220, 45, 45),
            (boss_bar_x, boss_bar_y, boss_fill_w, boss_bar_h),
            border_radius=6,
        )
        pygame.draw.rect(
            screen,
            (120, 60, 60),
            (boss_bar_x, boss_bar_y, boss_bar_w, boss_bar_h),
            width=2,
            border_radius=6,
        )

        boss_text = font.render(f"BOSS HP: {boss_hp}/{boss_max_hp}", True, (235, 235, 235))
        screen.blit(boss_text, (boss_bar_x + 10, boss_bar_y - 22))

        if state == "paused":
            overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 150))
            screen.blit(overlay, (0, 0))
            draw_text_center(screen, big_font, "PAUSED", HEIGHT * 0.45, (255, 255, 255))
            draw_text_center(screen, font, "Press P to Resume", HEIGHT * 0.56, (220, 220, 220))

        if state == "game_over":
            overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 170))
            screen.blit(overlay, (0, 0))
            draw_text_center(screen, big_font, "GAME OVER", HEIGHT * 0.42, (255, 255, 255))
            draw_text_center(screen, font, "Press R to Restart", HEIGHT * 0.54, (220, 220, 220))
            draw_text_center(screen, font, "Esc to Quit", HEIGHT * 0.60, (220, 220, 220))

        if state == "upgrade":
            overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 170))
            screen.blit(overlay, (0, 0))
            draw_text_center(screen, big_font, "LEVEL CLEARED", HEIGHT * 0.28, (255, 255, 255))
            draw_text_center(screen, font, "Choose 1 upgrade (click or press 1/2/3)", HEIGHT * 0.36, (220, 220, 220))

            up_rects = [
                pygame.Rect(WIDTH // 2 - 240, int(HEIGHT * 0.42), 480, 56),
                pygame.Rect(WIDTH // 2 - 240, int(HEIGHT * 0.52), 480, 56),
                pygame.Rect(WIDTH // 2 - 240, int(HEIGHT * 0.62), 480, 56),
            ]
            for i, r in enumerate(up_rects):
                if i < len(upgrade_choices):
                    uid, name, desc = upgrade_choices[i]
                    draw_button(screen, font, r, f"{i+1}. {name}  ({desc})")

        pygame.display.flip()

    pygame.quit()
    sys.exit(0)


if __name__ == "__main__":
    main()
